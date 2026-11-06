# agents/finance/agent.py
import re
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from common.llm import get_llm
from agents.base_agent import BaseAgent
from .tools import (
    init_finance_db,
    get_market_rates,
    calculate_mortgage,
    calculate_cash_flow,
    calculate_roi,
    project_5year,
    assess_risk,
    scenario_analysis,
    save_analysis,
)

# Prompt only for parameter extraction (deterministic)
EXTRACT_PROMPT = """You are a parameter extractor for a real estate analyzer.

Extract these parameters from user's message and return ONLY valid JSON (no markdown, no explanation):
{
  "city": "string (default: Karachi)",
  "property_price": number,
  "down_payment": number,
  "expected_rent": number,
  "interest_rate": number,
  "loan_years": number
}

Rules:
- If down_payment not given, use 30% of property_price
- If interest_rate not given, default 16
- If loan_years not given, default 15
- Numbers only, no PKR or commas or % signs
- Output ONLY the JSON, nothing else"""


class FinanceAgent(BaseAgent):
    NAME = "PropWealth"
    DESCRIPTION = "Real estate investment analyzer — mortgage, cash flow, ROI, 5-year projection, risk scoring, scenario analysis"
    ICON = "money_bag"
    DOMAIN = "Finance"
    
    def __init__(self):
        init_finance_db()
        self.llm = get_llm(temperature=0.1)
    
    def run(self, user_input: str, thread_id: str = "default", **kwargs) -> str:
        """Deterministic pipeline: Extract → Calculate All → Build Report."""
        
        try:
            # ─── Step 1: Extract parameters using LLM ───
            params = self._extract_params(user_input)
            
            if not params or 'property_price' not in params:
                return "❌ Could not extract property details. Please specify: city, price, rent, down payment, interest rate, loan years."
            
            # Apply defaults
            city = params.get('city', 'Karachi')
            property_price = float(params.get('property_price', 0))
            expected_rent = float(params.get('expected_rent', 0))
            down_payment = float(params.get('down_payment', property_price * 0.3))
            interest_rate = float(params.get('interest_rate', 16))
            loan_years = int(params.get('loan_years', 15))
            
            # ─── Step 2: Call ALL tools deterministically ───
            
            # 1. Market rates
            market_data = get_market_rates.invoke({"city": city})
            
            # Extract vacancy rate from market data
            vacancy_match = re.search(r'Vacancy Rate:\s*([\d.]+)%', market_data)
            vacancy_rate = float(vacancy_match.group(1)) / 100 if vacancy_match else 0.08
            
            # Extract appreciation rate
            appr_match = re.search(r'Appreciation:\s*([\d.]+)%', market_data)
            appreciation_rate = float(appr_match.group(1)) if appr_match else 8.0
            
            # 2. Mortgage
            mortgage = calculate_mortgage.invoke({
                "property_price": property_price,
                "down_payment": down_payment,
                "interest_rate": interest_rate,
                "loan_years": loan_years
            })
            
            # Extract EMI from mortgage output
            emi_match = re.search(r'Monthly EMI:\s*PKR\s*([\d,]+)', mortgage)
            monthly_emi = float(emi_match.group(1).replace(',', '')) if emi_match else 0
            
            # 3. Cash flow
            cash_flow = calculate_cash_flow.invoke({
                "monthly_rent": expected_rent,
                "monthly_emi": monthly_emi,
                "property_price": property_price,
                "vacancy_rate": vacancy_rate,
                "expenses_rate": 0.15
            })
            
            # Extract monthly cash flow
            cf_match = re.search(r'Monthly:\s*PKR\s*(-?[\d,]+)', cash_flow)
            monthly_cash_flow = float(cf_match.group(1).replace(',', '')) if cf_match else 0
            
            annual_cash_flow = monthly_cash_flow * 12
            annual_rent = expected_rent * 12
            
            # 4. ROI
            roi = calculate_roi.invoke({
                "property_price": property_price,
                "down_payment": down_payment,
                "annual_cash_flow": annual_cash_flow,
                "annual_rent": annual_rent,
                "appreciation_rate": appreciation_rate
            })
            
            # Extract ROI metrics
            cap_match = re.search(r'CAP RATE:\s*([\d.]+)%', roi)
            coc_match = re.search(r'CASH-ON-CASH RETURN:\s*([\d.]+)%', roi)
            cap_rate = float(cap_match.group(1)) if cap_match else 0
            cash_on_cash = float(coc_match.group(1)) if coc_match else 0
            
            # 5. 5-year projection
            projection = project_5year.invoke({
                "property_price": property_price,
                "down_payment": down_payment,
                "annual_cash_flow": annual_cash_flow,
                "appreciation_rate": appreciation_rate,
                "rent_growth": 5.0
            })
            
            # Extract 5-year ROI
            roi5_match = re.search(r'OVERALL 5-YEAR ROI:\s*([\d.-]+)%', projection)
            five_year_roi = float(roi5_match.group(1)) if roi5_match else 0
            
            # 6. Risk assessment
            risk = assess_risk.invoke({
                "property_price": property_price,
                "monthly_cash_flow": monthly_cash_flow,
                "vacancy_rate": vacancy_rate,
                "interest_rate": interest_rate
            })
            
            # Extract risk score
            risk_match = re.search(r'Score:\s*(\d+)/10', risk)
            risk_score = float(risk_match.group(1)) if risk_match else 5
            
            # 7. Scenario analysis
            scenarios = scenario_analysis.invoke({
                "property_price": property_price,
                "down_payment": down_payment,
                "monthly_rent": expected_rent,
                "monthly_emi": monthly_emi,
                "base_cash_flow": monthly_cash_flow
            })

            # Use the same recommendation criteria as the final report.
            if risk_score > 7 or monthly_cash_flow < -50000:
                recommendation = "AVOID"
            elif risk_score > 5 or monthly_cash_flow < 0:
                recommendation = "HOLD"
            elif five_year_roi > 20:
                recommendation = "STRONG BUY"
            else:
                recommendation = "BUY"
            
            # 8. Save analysis
            # 8. Save analysis (with explicit error handling)
            try:
                save_result = save_analysis.invoke({
                    "property_price": property_price,
                    "location": city,
                    "expected_rent": expected_rent,
                    "down_payment": down_payment,
                    "interest_rate": interest_rate,
                    "loan_years": loan_years,
                    "monthly_emi": monthly_emi,
                    "monthly_cash_flow": monthly_cash_flow,
                    "cap_rate": cap_rate,
                    "cash_on_cash": cash_on_cash,
                    "five_year_roi": five_year_roi,
                    "risk_score": risk_score,
                    "recommendation": f"{recommendation} - Risk: {risk_score}/10, ROI: {five_year_roi}%"
                })
                print(f"DB SAVE: {save_result}")  # Console log for debugging
                save_status = "✅ Analysis saved to database"
            except Exception as save_err:
                print(f"DB SAVE ERROR: {save_err}")
                save_status = f"⚠️ Could not save to DB: {save_err}"
            
            # ─── Step 3: Build Final Report ───
            return self._build_report(
                city=city,
                property_price=property_price,
                down_payment=down_payment,
                expected_rent=expected_rent,
                interest_rate=interest_rate,
                loan_years=loan_years,
                market_data=market_data,
                mortgage=mortgage,
                cash_flow=cash_flow,
                roi=roi,
                projection=projection,
                risk=risk,
                scenarios=scenarios,
                monthly_cash_flow=monthly_cash_flow,
                monthly_emi=monthly_emi,
                risk_score=risk_score,
                five_year_roi=five_year_roi
            )
            
        except Exception as e:
            return f"❌ Error generating report: {str(e)}\n\nPlease ensure you provide: city, property price, expected rent, down payment, interest rate, and loan tenure."
    
    def _extract_params(self, user_input: str) -> dict:
        """Use LLM to extract structured parameters from user input."""
        try:
            response = self.llm.invoke([
                SystemMessage(content=EXTRACT_PROMPT),
                HumanMessage(content=user_input)
            ])
            
            # Clean response - remove markdown
            content = response.content.strip()
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            
            return json.loads(content)
        except Exception as e:
            print(f"Extraction error: {e}")
            return {}
    
    def _build_report(self, **kwargs) -> str:
        """Build clean formatted report."""
        
        cf_emoji = "✅" if kwargs['monthly_cash_flow'] > 0 else "❌"
        risk_emoji = "🟢" if kwargs['risk_score'] <= 3 else "🟡" if kwargs['risk_score'] <= 6 else "🔴"
        
        # Recommendation logic
        if kwargs['risk_score'] > 7 or kwargs['monthly_cash_flow'] < -50000:
            recommendation = "AVOID"
            reason = "High risk and negative cash flow make this a poor investment."
        elif kwargs['risk_score'] > 5 or kwargs['monthly_cash_flow'] < 0:
            recommendation = "HOLD"
            reason = "Moderate risk with cash flow concerns. Consider higher down payment."
        elif kwargs['five_year_roi'] > 20:
            recommendation = "STRONG BUY"
            reason = "Excellent ROI projection with manageable risk."
        else:
            recommendation = "BUY"
            reason = "Solid investment with positive metrics."
        
        report = f"""
============================================================
   PROPERTY INVESTMENT ANALYSIS REPORT
============================================================

PROPERTY DETAILS:
  Location: {kwargs['city']}
  Property Price: PKR {kwargs['property_price']:,.0f}
  Down Payment: PKR {kwargs['down_payment']:,.0f} ({(kwargs['down_payment']/kwargs['property_price'])*100:.1f}%)
  Loan Amount: PKR {kwargs['property_price'] - kwargs['down_payment']:,.0f}
  Expected Rent: PKR {kwargs['expected_rent']:,.0f}/month
  Interest Rate: {kwargs['interest_rate']}%
  Loan Tenure: {kwargs['loan_years']} years

------------------------------------------------------------
MARKET DATA ({kwargs['city']})
------------------------------------------------------------
{kwargs['market_data']}

------------------------------------------------------------
MORTGAGE SUMMARY
------------------------------------------------------------
{kwargs['mortgage']}

------------------------------------------------------------
CASH FLOW ANALYSIS  {cf_emoji}
------------------------------------------------------------
{kwargs['cash_flow']}

------------------------------------------------------------
ROI METRICS
------------------------------------------------------------
{kwargs['roi']}

------------------------------------------------------------
5-YEAR PROJECTION
------------------------------------------------------------
{kwargs['projection']}

------------------------------------------------------------
RISK ASSESSMENT  {risk_emoji}
------------------------------------------------------------
{kwargs['risk']}

------------------------------------------------------------
SCENARIO ANALYSIS
------------------------------------------------------------
{kwargs['scenarios']}

============================================================
FINAL RECOMMENDATION: {recommendation}
------------------------------------------------------------
{reason}

Risk Score: {kwargs['risk_score']}/10
Monthly Cash Flow: PKR {kwargs['monthly_cash_flow']:,.0f}
5-Year ROI: {kwargs['five_year_roi']:.1f}%

============================================================
DISCLAIMER: This is analysis only, NOT financial advice.
Consult a licensed financial advisor before investing.
============================================================
"""
        return report
    
    def render_ui(self):
        from .ui import render_finance_ui
        render_finance_ui(self)