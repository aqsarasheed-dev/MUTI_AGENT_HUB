# agents/finance/tools.py
import sqlite3
import json
from langchain_core.tools import tool
from functools import lru_cache

# ─── Database Setup ─────────────────────────────────────
DB_PATH = "database/finance.db"

@lru_cache(maxsize=1)
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_finance_db():
    """Create tables and seed market data. Run once."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS market_rates (
            id INTEGER PRIMARY KEY,
            city TEXT NOT NULL,
            avg_rent_per_sqft REAL,
            appreciation_rate REAL,
            vacancy_rate REAL,
            property_tax_rate REAL
        );
        
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_price REAL,
            location TEXT,
            expected_rent REAL,
            down_payment REAL,
            interest_rate REAL,
            loan_years INTEGER,
            monthly_emi REAL,
            monthly_cash_flow REAL,
            cap_rate REAL,
            cash_on_cash REAL,
            five_year_roi REAL,
            risk_score REAL,
            recommendation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # ─── Seed Market Rates (Pakistan Cities) ───
    count = db.execute("SELECT COUNT(*) FROM market_rates").fetchone()[0]
    if count == 0:
        cities = [
            ("Karachi", 35.0, 0.08, 0.08, 0.05),    # rent/sqft, appreciation, vacancy, tax
            ("Lahore", 30.0, 0.10, 0.06, 0.04),
            ("Islamabad", 40.0, 0.12, 0.05, 0.04),
            ("Rawalpindi", 25.0, 0.09, 0.07, 0.04),
            ("Faisalabad", 20.0, 0.07, 0.08, 0.04),
            ("Multan", 22.0, 0.08, 0.07, 0.04),
            ("Peshawar", 24.0, 0.08, 0.08, 0.04),
            ("Hyderabad", 26.0, 0.08, 0.07, 0.04),
            ("Quetta", 23.0, 0.07, 0.09, 0.04),
            ("Gujranwala", 21.0, 0.08, 0.07, 0.04),
        ]
        db.executemany(
            "INSERT INTO market_rates (city, avg_rent_per_sqft, appreciation_rate, vacancy_rate, property_tax_rate) "
            "VALUES (?, ?, ?, ?, ?)",
            cities
        )
    
    db.commit()


# ─── Tools ──────────────────────────────────────────────

@tool
def get_market_rates(city: str) -> str:
    """Get current real estate market rates for a Pakistan city.
    
    Args:
        city: City name (Karachi, Lahore, Islamabad, Rawalpindi, Faisalabad, Multan, Peshawar, Hyderabad, Quetta, Gujranwala)
    
    Returns:
        Average rent per sqft, appreciation rate, vacancy rate, property tax rate.
    """
    db = get_db()
    row = db.execute(
        "SELECT * FROM market_rates WHERE city LIKE ?",
        (f"%{city}%",)
    ).fetchone()
    
    if not row:
        return f"City '{city}' not found. Available: Karachi, Lahore, Islamabad, Rawalpindi, Faisalabad, Multan, Peshawar, Hyderabad, Quetta, Gujranwala"
    
    return (
        f"Market Data for {row['city']}:\n"
        f"  Average Rent: PKR {row['avg_rent_per_sqft']:.0f}/sqft/month\n"
        f"  Annual Appreciation: {row['appreciation_rate']*100:.1f}%\n"
        f"  Vacancy Rate: {row['vacancy_rate']*100:.1f}%\n"
        f"  Property Tax: {row['property_tax_rate']*100:.1f}%/year"
    )


@tool
def calculate_mortgage(
    property_price: float,
    down_payment: float,
    interest_rate: float,
    loan_years: int
) -> str:
    """Calculate monthly mortgage payment (EMI) using standard formula.
    
    Args:
        property_price: Total property price in PKR
        down_payment: Down payment amount in PKR
        interest_rate: Annual interest rate as percentage (e.g., 15 for 15%)
        loan_years: Loan tenure in years (e.g., 10, 15, 20)
    
    Returns:
        Loan amount, monthly EMI, total interest, total payment.
    """
    loan_amount = property_price - down_payment
    monthly_rate = (interest_rate / 100) / 12
    num_payments = loan_years * 12
    
    if monthly_rate == 0:
        emi = loan_amount / num_payments
    else:
        emi = loan_amount * monthly_rate * (1 + monthly_rate) ** num_payments / \
              ((1 + monthly_rate) ** num_payments - 1)
    
    total_payment = emi * num_payments
    total_interest = total_payment - loan_amount
    
    return (
        f"Mortgage Calculation:\n"
        f"  Property Price: PKR {property_price:,.0f}\n"
        f"  Down Payment: PKR {down_payment:,.0f} ({(down_payment/property_price)*100:.1f}%)\n"
        f"  Loan Amount: PKR {loan_amount:,.0f}\n"
        f"  Interest Rate: {interest_rate}%/year\n"
        f"  Loan Tenure: {loan_years} years ({num_payments} months)\n\n"
        f"  Monthly EMI: PKR {emi:,.0f}\n"
        f"  Total Payment: PKR {total_payment:,.0f}\n"
        f"  Total Interest: PKR {total_interest:,.0f}\n"
        f"  Interest as % of loan: {(total_interest/loan_amount)*100:.1f}%"
    )


@tool
def calculate_cash_flow(
    monthly_rent: float,
    monthly_emi: float,
    property_price: float,
    vacancy_rate: float = 0.08,
    expenses_rate: float = 0.15
) -> str:
    """Calculate monthly and annual cash flow for rental property.
    
    Args:
        monthly_rent: Expected monthly rent in PKR
        monthly_emi: Monthly mortgage payment in PKR
        property_price: Property price in PKR (for tax calculation)
        vacancy_rate: Vacancy rate as decimal (default 0.08 = 8%)
        expenses_rate: Maintenance + management expenses as decimal (default 0.15 = 15% of rent)
    
    Returns:
        Monthly/annual cash flow breakdown with all expenses.
    """
    # Gross income
    gross_monthly = monthly_rent
    gross_annual = monthly_rent * 12
    
    # Vacancy loss
    vacancy_loss_monthly = monthly_rent * vacancy_rate
    vacancy_loss_annual = vacancy_loss_monthly * 12
    
    # Operating expenses (maintenance, management, insurance)
    expenses_monthly = monthly_rent * expenses_rate
    expenses_annual = expenses_monthly * 12
    
    # Property tax (assume 4% of price per year)
    property_tax_annual = property_price * 0.04
    property_tax_monthly = property_tax_annual / 12
    
    # Net operating income
    noi_monthly = gross_monthly - vacancy_loss_monthly - expenses_monthly - property_tax_monthly
    noi_annual = noi_monthly * 12
    
    # Cash flow after mortgage
    cash_flow_monthly = noi_monthly - monthly_emi
    cash_flow_annual = cash_flow_monthly * 12
    
    return (
        f"Cash Flow Analysis:\n\n"
        f"INCOME:\n"
        f"  Gross Monthly Rent: PKR {gross_monthly:,.0f}\n"
        f"  Gross Annual Rent: PKR {gross_annual:,.0f}\n\n"
        f"EXPENSES (Monthly):\n"
        f"  Vacancy Loss ({vacancy_rate*100:.0f}%): -PKR {vacancy_loss_monthly:,.0f}\n"
        f"  Operating Expenses ({expenses_rate*100:.0f}%): -PKR {expenses_monthly:,.0f}\n"
        f"  Property Tax (4%/yr): -PKR {property_tax_monthly:,.0f}\n"
        f"  Mortgage EMI: -PKR {monthly_emi:,.0f}\n\n"
        f"NET CASH FLOW:\n"
        f"  Monthly: PKR {cash_flow_monthly:,.0f}\n"
        f"  Annual: PKR {cash_flow_annual:,.0f}\n\n"
        f"{'✅ POSITIVE cash flow' if cash_flow_monthly > 0 else '❌ NEGATIVE cash flow'} "
        f"(needs subsidy from owner)"
    )


@tool
def calculate_roi(
    property_price: float,
    down_payment: float,
    annual_cash_flow: float,
    annual_rent: float,
    appreciation_rate: float = 0.08
) -> str:
    """Calculate key ROI metrics: Cap Rate, Cash-on-Cash Return, Total ROI.
    
    Args:
        property_price: Total property price in PKR
        down_payment: Down payment (initial investment) in PKR
        annual_cash_flow: Annual cash flow after all expenses + mortgage
        annual_rent: Gross annual rent
        appreciation_rate: Expected annual appreciation (default 8%)
    
    Returns:
        Cap Rate, Cash-on-Cash Return, Total ROI with explanations.
    """
    # Cap Rate = NOI / Property Price (use rent as proxy for NOI simplified)
    noi = annual_rent * 0.65  # assume 35% expenses
    cap_rate = (noi / property_price) * 100
    
    # Cash-on-Cash Return = Annual Cash Flow / Cash Invested (down payment)
    cash_on_cash = (annual_cash_flow / down_payment) * 100 if down_payment > 0 else 0
    
    # Total ROI = (Cash Flow + Appreciation) / Cash Invested
    annual_appreciation = property_price * (appreciation_rate / 100)
    total_roi = ((annual_cash_flow + annual_appreciation) / down_payment) * 100 if down_payment > 0 else 0
    
    return (
        f"ROI Metrics:\n\n"
        f"1. CAP RATE: {cap_rate:.2f}%\n"
        f"   Formula: NOI / Property Price\n"
        f"   NOI (estimated): PKR {noi:,.0f}\n"
        f"   Interpretation: {'GOOD' if cap_rate > 6 else 'FAIR' if cap_rate > 4 else 'POOR'} "
        f"(>6% is good for PK market)\n\n"
        f"2. CASH-ON-CASH RETURN: {cash_on_cash:.2f}%\n"
        f"   Formula: Annual Cash Flow / Down Payment\n"
        f"   Interpretation: {'EXCELLENT' if cash_on_cash > 10 else 'GOOD' if cash_on_cash > 5 else 'POOR'} "
        f"(>10% is excellent)\n\n"
        f"3. TOTAL ROI (with appreciation): {total_roi:.2f}%\n"
        f"   Formula: (Cash Flow + Appreciation) / Down Payment\n"
        f"   Annual Appreciation: PKR {annual_appreciation:,.0f} ({appreciation_rate}%)\n"
        f"   Interpretation: {'EXCELLENT' if total_roi > 20 else 'GOOD' if total_roi > 15 else 'FAIR'} "
        f"(>20% is excellent)\n\n"
        f"SUMMARY:\n"
        f"  Annual Cash Flow: PKR {annual_cash_flow:,.0f}\n"
        f"  Annual Appreciation: PKR {annual_appreciation:,.0f}\n"
        f"  Total Annual Gain: PKR {annual_cash_flow + annual_appreciation:,.0f}\n"
        f"  On Investment of: PKR {down_payment:,.0f}\n"
        f"  Total ROI: {total_roi:.1f}%"
    )


@tool
def project_5year(
    property_price: float,
    down_payment: float,
    annual_cash_flow: float,
    appreciation_rate: float = 8.0,  # Changed: now expects percentage (8 = 8%)
    rent_growth: float = 5.0  # Changed: now expects percentage (5 = 5%)
) -> str:
    """Project 5-year investment performance with appreciation + rent growth.
    
    Args:
        property_price: Initial property price in PKR
        down_payment: Initial investment in PKR
        annual_cash_flow: Year 1 annual cash flow
        appreciation_rate: Annual property appreciation in PERCENT (e.g., 8 for 8%, NOT 0.08)
        rent_growth: Annual rent growth in PERCENT (e.g., 5 for 5%)
    """
    current_value = property_price
    current_cash_flow = annual_cash_flow
    total_cash_flow = 0
    loan_balance = property_price - down_payment
    
    results = []
    results.append(f"5-Year Projection (Appreciation: {appreciation_rate}%, Rent Growth: {rent_growth}%):\n")
    results.append(f"{'Year':<6}{'Value':<15}{'Cash Flow':<15}{'Equity':<15}{'Total ROI':<12}")
    results.append("-" * 63)
    
    for year in range(1, 6):
        current_value *= (1 + appreciation_rate / 100)  # Convert percent to decimal
        current_cash_flow *= (1 + rent_growth / 100)
        total_cash_flow += current_cash_flow
        equity = current_value - loan_balance
        total_roi = ((total_cash_flow + (current_value - property_price)) / down_payment) * 100
        
        results.append(
            f"{year:<6}"
            f"PKR {current_value/1000000:.1f}M    "
            f"PKR {current_cash_flow/1000:.0f}K      "
            f"PKR {equity/1000000:.1f}M    "
            f"{total_roi:.1f}%"
        )
    
    final_value = current_value
    total_gain = total_cash_flow + (final_value - property_price)
    overall_roi = (total_gain / down_payment) * 100
    
    results.append("-" * 63)
    results.append(f"\n5-YEAR SUMMARY:")
    results.append(f"  Initial Investment: PKR {down_payment:,.0f}")
    results.append(f"  Final Property Value: PKR {final_value:,.0f}")
    results.append(f"  Total Cash Flow (5yr): PKR {total_cash_flow:,.0f}")
    results.append(f"  Total Appreciation: PKR {final_value - property_price:,.0f}")
    results.append(f"  TOTAL GAIN: PKR {total_gain:,.0f}")
    results.append(f"  OVERALL 5-YEAR ROI: {overall_roi:.1f}%")
    results.append(f"  ANNUALIZED ROI: {overall_roi/5:.1f}%")
    
    return "\n".join(results)


@tool
def assess_risk(
    property_price: float,
    monthly_cash_flow: float,
    vacancy_rate: float = 0.08,
    interest_rate: float = 15.0
) -> str:
    """Assess investment risk score (1-10) based on multiple factors.
    
    Args:
        property_price: Property price in PKR
        monthly_cash_flow: Monthly cash flow (can be negative)
        vacancy_rate: Market vacancy rate as decimal (default 8%)
        interest_rate: Mortgage interest rate (default 15%)
    
    Returns:
        Risk score (1=low risk, 10=high risk) with breakdown + mitigation.
    """
    risks = []
    score = 0
    
    # Cash flow risk
    if monthly_cash_flow < 0:
        score += 3
        risks.append(f"⚠️ NEGATIVE cash flow (-PKR {abs(monthly_cash_flow):,.0f}/mo) — HIGH RISK")
    elif monthly_cash_flow < 5000:
        score += 2
        risks.append(f"⚠️ Low cash flow (PKR {monthly_cash_flow:,.0f}/mo) — thin margin")
    else:
        risks.append(f"✅ Healthy cash flow (PKR {monthly_cash_flow:,.0f}/mo)")
    
    # Vacancy risk
    if vacancy_rate > 0.10:
        score += 2
        risks.append(f"⚠️ High vacancy rate ({vacancy_rate*100:.0f}%) — tenant risk")
    elif vacancy_rate > 0.07:
        score += 1
        risks.append(f"⚠️ Moderate vacancy rate ({vacancy_rate*100:.0f}%)")
    else:
        risks.append(f"✅ Low vacancy rate ({vacancy_rate*100:.0f}%)")
    
    # Interest rate risk
    if interest_rate > 18:
        score += 2
        risks.append(f"⚠️ High interest rate ({interest_rate}%) — financing risk")
    elif interest_rate > 15:
        score += 1
        risks.append(f"⚠️ Moderate interest rate ({interest_rate}%)")
    
    # Price concentration risk (assume > 20M is high ticket)
    if property_price > 20000000:
        score += 1
        risks.append(f"⚠️ High-ticket property (PKR {property_price/1000000:.1f}M) — liquidity risk")
    
    # Cap score to 10
    score = min(score, 10)
    
    if score <= 3:
        risk_level = "LOW RISK"
        recommendation = "Safe investment, proceed with standard due diligence."
    elif score <= 6:
        risk_level = "MODERATE RISK"
        recommendation = "Acceptable, but monitor cash flow closely. Build emergency fund (3-6 months expenses)."
    else:
        risk_level = "HIGH RISK"
        recommendation = "Consider renegotiating price, increasing down payment, or reconsidering investment."
    
    result = f"RISK ASSESSMENT: {risk_level} (Score: {score}/10)\n\n"
    result += "RISK FACTORS:\n"
    for r in risks:
        result += f"  {r}\n"
    result += f"\nRECOMMENDATION: {recommendation}"
    
    return result


@tool
def scenario_analysis(
    property_price: float,
    down_payment: float,
    monthly_rent: float,
    monthly_emi: float,
    base_cash_flow: float
) -> str:
    """Run what-if scenarios: rent drops, vacancy increases, interest rises.
    
    Args:
        property_price: Property price in PKR
        down_payment: Down payment in PKR
        monthly_rent: Current monthly rent
        monthly_emi: Monthly mortgage payment
        base_cash_flow: Current monthly cash flow
    
    Returns:
        3 scenarios: Worst case, Base case, Best case with impact analysis.
    """
    # Worst case: rent drops 15%, vacancy 12%
    worst_rent = monthly_rent * 0.85
    worst_vacancy = monthly_rent * 0.12
    worst_expenses = worst_rent * 0.15
    worst_tax = (property_price * 0.04) / 12
    worst_cash_flow = worst_rent - worst_vacancy - worst_expenses - worst_tax - monthly_emi
    
    # Best case: rent increases 10%, vacancy 4%
    best_rent = monthly_rent * 1.10
    best_vacancy = monthly_rent * 0.04
    best_expenses = best_rent * 0.15
    best_tax = (property_price * 0.04) / 12
    best_cash_flow = best_rent - best_vacancy - best_expenses - best_tax - monthly_emi
    
    return (
        f"SCENARIO ANALYSIS:\n\n"
        f"{'Scenario':<15}{'Rent':<12}{'Vacancy':<10}{'Cash Flow':<15}{'vs Base':<12}\n"
        f"{'-'*64}\n"
        f"{'Worst Case':<15}"
        f"PKR {worst_rent:,.0f}  "
        f"{'12%':<10}"
        f"PKR {worst_cash_flow:,.0f}    "
        f"{((worst_cash_flow-base_cash_flow)/abs(base_cash_flow)*100) if base_cash_flow != 0 else 0:.1f}%\n"
        f"{'Base Case':<15}"
        f"PKR {monthly_rent:,.0f}  "
        f"{'8%':<10}"
        f"PKR {base_cash_flow:,.0f}    "
        f"0%\n"
        f"{'Best Case':<15}"
        f"PKR {best_rent:,.0f}  "
        f"{'4%':<10}"
        f"PKR {best_cash_flow:,.0f}    "
        f"{((best_cash_flow-base_cash_flow)/abs(base_cash_flow)*100) if base_cash_flow != 0 else 0:.1f}%\n"
        f"{'-'*64}\n\n"
        f"ANALYSIS:\n"
        f"  Worst case: {'SURVIVABLE' if worst_cash_flow > -10000 else 'CRITICAL — needs subsidy'}\n"
        f"  Best case upside: PKR {best_cash_flow - base_cash_flow:,.0f}/mo extra\n"
        f"  Risk tolerance check: Can you sustain PKR {abs(worst_cash_flow):,.0f}/mo loss for 6 months?"
    )


@tool
def save_analysis(
    property_price: float,
    location: str,
    expected_rent: float,
    down_payment: float,
    interest_rate: float,
    loan_years: int,
    monthly_emi: float,
    monthly_cash_flow: float,
    cap_rate: float,
    cash_on_cash: float,
    five_year_roi: float,
    risk_score: float,
    recommendation: str
) -> str:
    """Save complete property analysis to database for future reference.
    
    Args:
        property_price: Property price
        location: City/location name
        expected_rent: Monthly expected rent
        down_payment: Down payment amount
        interest_rate: Interest rate %
        loan_years: Loan tenure years
        monthly_emi: Calculated EMI
        monthly_cash_flow: Monthly cash flow
        cap_rate: Cap rate %
        cash_on_cash: Cash-on-cash return %
        five_year_roi: 5-year ROI %
        risk_score: Risk score 1-10
        recommendation: Final recommendation text
    """
    db = get_db()
    db.execute(
        """INSERT INTO analyses 
           (property_price, location, expected_rent, down_payment, interest_rate, 
            loan_years, monthly_emi, monthly_cash_flow, cap_rate, cash_on_cash, 
            five_year_roi, risk_score, recommendation)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (property_price, location, expected_rent, down_payment, interest_rate,
         loan_years, monthly_emi, monthly_cash_flow, cap_rate, cash_on_cash,
         five_year_roi, risk_score, recommendation)
    )
    db.commit()
    return f"Analysis saved! Property: PKR {property_price:,.0f} in {location}"


@tool
def get_analysis_history(limit: int = 5) -> str:
    """Get past property analyses for comparison.
    
    Args:
        limit: Number of past analyses to retrieve (default 5)
    
    Returns:
        List of past analyses with key metrics.
    """
    db = get_db()
    rows = db.execute(
        "SELECT * FROM analyses ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    
    if not rows:
        return "No past analyses yet."
    
    results = []
    for r in rows:
        results.append(
            f"ID: {r['id']} | {r['location']} | PKR {r['property_price']:,.0f}\n"
            f"  Rent: PKR {r['expected_rent']:,.0f}/mo | Cash Flow: PKR {r['monthly_cash_flow']:,.0f}/mo\n"
            f"  Cap Rate: {r['cap_rate']:.1f}% | Cash-on-Cash: {r['cash_on_cash']:.1f}%\n"
            f"  5-Year ROI: {r['five_year_roi']:.1f}% | Risk: {r['risk_score']}/10\n"
            f"  Date: {r['created_at']}"
        )
    
    return "\n\n".join(results)


# ─── All Tools List ─────────────────────────────────────
ALL_TOOLS = [
    get_market_rates,
    calculate_mortgage,
    calculate_cash_flow,
    calculate_roi,
    project_5year,
    assess_risk,
    scenario_analysis,
    save_analysis,
    get_analysis_history,
]