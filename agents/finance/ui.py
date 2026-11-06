# agents/finance/ui.py
import streamlit as st

def render_finance_ui(agent):
    """Streamlit UI for PropWealth finance agent."""
    
    st.markdown("### 💰 PropWealth — Property Investment Analyzer")
    st.markdown("Analyze real estate investments: mortgage, cash flow, ROI, 5-year projection, risk assessment.")
    
    # ─── Input Form ────────────────────────────────────
    st.markdown("#### 🏠 Property Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        location = st.selectbox(
            "📍 City",
            ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", 
             "Multan", "Peshawar", "Hyderabad", "Quetta", "Gujranwala"]
        )
        property_price = st.number_input(
            "💵 Property Price (PKR)",
            min_value=1000000,
            max_value=100000000,
            value=15000000,
            step=500000,
            format="%d"
        )
        expected_rent = st.number_input(
            "🏠 Expected Monthly Rent (PKR)",
            min_value=10000,
            max_value=500000,
            value=80000,
            step=5000,
            format="%d"
        )
    
    with col2:
        down_payment = st.number_input(
            "💳 Down Payment (PKR)",
            min_value=0,
            max_value=property_price,
            value=int(property_price * 0.3),
            step=500000,
            format="%d"
        )
        interest_rate = st.slider(
            "📊 Interest Rate (%)",
            min_value=10.0,
            max_value=25.0,
            value=16.0,
            step=0.5,
            help="Pakistan banks typically charge 14-18% for mortgage"
        )
        loan_years = st.slider(
            "📅 Loan Tenure (years)",
            min_value=5,
            max_value=25,
            value=15,
            step=5
        )
    
    # ─── Market Info ───────────────────────────────────
    with st.expander("ℹ️ Market Info (auto-fetched from city)"):
        st.markdown(f"**Selected City:** {location}")
        st.markdown("The agent will automatically fetch vacancy rate, appreciation rate, and property tax for this city.")
    
    # ─── Build User Input ──────────────────────────────
    user_input = f"""
Please analyze this property investment:

Location: {location}
Property Price: PKR {property_price:,}
Down Payment: PKR {down_payment:,} ({(down_payment/property_price)*100:.1f}%)
Expected Monthly Rent: PKR {expected_rent:,}
Interest Rate: {interest_rate}%
Loan Tenure: {loan_years} years

Please provide complete analysis with:
1. Mortgage calculation (EMI)
2. Cash flow analysis
3. ROI metrics (Cap Rate, Cash-on-Cash, Total ROI)
4. 5-year projection
5. Risk assessment
6. Scenario analysis (worst/base/best case)
7. Final recommendation
"""
    
    # ─── Run Button ────────────────────────────────────
    if st.button("📊 Analyze Investment", type="primary", use_container_width=True):
        with st.spinner(f"Analyzing property in {location}..."):
            try:
                response = agent.run(
                    user_input,
                    thread_id=f"finance-{location}-{property_price}-{hash(user_input) % 10000}"
                )
                
                st.markdown("---")
                st.markdown("### 📊 Investment Analysis Report")
                st.markdown(response)
                
                # Save to history
                if "finance_history" not in st.session_state:
                    st.session_state.finance_history = []
                
                st.session_state.finance_history.append({
                    "location": location,
                    "price": property_price,
                    "rent": expected_rent,
                    "response": response
                })
                
            except Exception as e:
                st.error(f"Error: {e}")
    
    # ─── Quick Examples ────────────────────────────────
    st.markdown("---")
    st.markdown("### 💡 Quick Examples")
    
    examples = [
        ("🏠 Karachi Apartment", "Analyze 15M PKR apartment in Karachi, 80K rent, 30% down, 16% interest, 15yr loan"),
        ("🏠 Lahore House", "Analyze 25M PKR house in Lahore, 120K rent, 25% down, 15% interest, 20yr loan"),
        ("🏠 Islamabad Plot+Build", "Analyze 35M PKR property in Islamabad, 180K rent, 40% down, 14% interest, 15yr loan"),
        ("🏠 Faisalabad Commercial", "Analyze 10M PKR commercial property in Faisalabad, 70K rent, 35% down, 17% interest, 10yr loan"),
    ]
    
    cols = st.columns(len(examples))
    for col, (label, prompt) in zip(cols, examples):
        if col.button(label, key=f"fin_ex_{label}"):
            st.session_state.finance_quick_prompt = prompt
    
    # Handle quick prompt
    if "finance_quick_prompt" in st.session_state:
        prompt = st.session_state.finance_quick_prompt
        del st.session_state.finance_quick_prompt
        
        with st.spinner("Analyzing..."):
            try:
                response = agent.run(
                    prompt,
                    thread_id=f"finance-quick-{hash(prompt) % 10000}"
                )
                
                st.markdown("---")
                st.markdown("### 📊 Investment Analysis Report")
                st.markdown(response)
                
                if "finance_history" not in st.session_state:
                    st.session_state.finance_history = []
                
                st.session_state.finance_history.append({
                    "location": "Quick example",
                    "price": 0,
                    "rent": 0,
                    "response": response
                })
            except Exception as e:
                st.error(f"Error: {e}")
    
    # ─── Disclaimer ────────────────────────────────────
    st.markdown("---")
    st.warning(
        "⚠️ **DISCLAIMER:** This tool provides analysis only, NOT financial advice. "
        "Always consult a licensed financial advisor before making investment decisions. "
        "Real estate investments carry risk; past performance doesn't guarantee future returns."
    )
        # ─── Database History (Actual DB records) ─────────
    st.markdown("---")
    st.markdown("### 🗄️ Database History (All Saved Analyses)")
    
    if st.button("📂 View Saved Analyses from Database"):
        with st.spinner("Fetching from database..."):
            try:
                from agents.finance.tools import get_analysis_history
                db_history = get_analysis_history.invoke({"limit": 10})
                st.code(db_history)
            except Exception as e:
                st.error(f"Error fetching DB history: {e}")
    
    # Show DB file info
    import os
    db_path = "database/finance.db"
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path) / 1024
        st.caption(f"📁 Database: `{db_path}` ({db_size:.1f} KB)")
    else:
        st.warning("⚠️ Database file not found! Analyses won't be saved.")
    # ─── History ───────────────────────────────────────
    if st.session_state.get("finance_history"):
        st.markdown("---")
        st.markdown("### 📜 Recent Analyses")
        
        for i, item in enumerate(reversed(st.session_state.finance_history[-5:])):
            title = f"{item['location']} - PKR {item['price']/1000000:.1f}M" if item['price'] > 0 else item['location']
            with st.expander(f"Analysis {i+1}: {title}"):
                st.markdown(item["response"])