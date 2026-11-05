# agents/researcher/ui.py
import streamlit as st

def render_researcher_ui(agent):
    """Streamlit UI for News Researcher agent."""
    
    st.markdown("### 🔍 News Researcher")
    st.markdown("Search news, get summaries, check stock prices, calculate gains.")
    
    # Query type selector
    query_type = st.selectbox(
        "What do you want to do?",
        ["📰 Search News", "📈 Get Stock Price", "💰 Calculate Gain", "🔎 Mixed Query"]
    )
    
    # Input based on type
    user_input = st.text_area(
        "Your query:",
        placeholder="e.g., Latest AI news OR AAPL stock price OR I bought AAPL at $150, now it's $180",
        height=80
    )
    
    # Run button
    if st.button("🚀 Run Query", type="primary"):
        if not user_input.strip():
            st.warning("Please enter a query first.")
            return
        
        # Generate thread_id (use session state for continuity)
        thread_id = st.session_state.get("thread_id", f"user-{hash(user_input) % 10000}")
        st.session_state.thread_id = thread_id
        
        with st.spinner("Researching..."):
            try:
                response = agent.run(user_input, thread_id=thread_id)
                
                st.markdown("---")
                st.markdown("### 📋 Response")
                st.markdown(response)
                
                # Save to history
                if "researcher_history" not in st.session_state:
                    st.session_state.researcher_history = []
                st.session_state.researcher_history.append({
                    "query": user_input,
                    "response": response,
                    "type": query_type
                })
                
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Show history
    if st.session_state.get("researcher_history"):
        st.markdown("---")
        st.markdown("### 📜 Recent Queries")
        for i, item in enumerate(reversed(st.session_state.researcher_history[-5:])):
            with st.expander(f"Q{len(st.session_state.researcher_history) - i}: {item['query'][:60]}..."):
                st.markdown(item["response"])