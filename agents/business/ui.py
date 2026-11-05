# agents/ecommerce/ui.py
import streamlit as st

def render_ecommerce_ui(agent):
    """Streamlit UI for EmailCraft Writer + Reviewer agent."""
    
    st.markdown("### 📧 EmailCraft — Writer + Reviewer")
    st.markdown("Writer agent drafts your email, Reviewer agent scores it, and Writer revises until all scores are 7+.")
    
    # ─── Email Type Selector ───────────────────────────
    email_type = st.selectbox(
        "📧 Email Type",
        ["Welcome", "Sales", "Newsletter", "Re-engagement", 
         "Support", "Thank You", "Abandoned Cart", "Other"],
        help="Select the type of email you want to write"
    )
    
    # ─── Brief Input ───────────────────────────────────
    brief_placeholder = {
        "Welcome": "e.g., Welcome email for new SaaS signup, offer 14-day free trial",
        "Sales": "e.g., Cold email to CEO of fintech startup, offering AI chatbot solution",
        "Newsletter": "e.g., Weekly newsletter for AI/ML community, summarizing top 5 trends",
        "Re-engagement": "e.g., Users who haven't logged in for 30 days, offer 50% off",
        "Support": "e.g., Follow-up on ticket #12345 about login issue, provide fix steps",
        "Thank You": "e.g., Thank you for purchase of $89, order #ORD-789",
        "Abandoned Cart": "e.g., User left iPhone case in cart, offer 10% off to complete",
        "Other": "Describe your email brief in detail"
    }
    
    user_input = st.text_area(
        "✍️ Email Brief",
        placeholder=brief_placeholder.get(email_type, "Describe your email brief..."),
        height=100,
        help="Be specific: target audience, goal, key message, any offer"
    )
    
    # ─── Settings ──────────────────────────────────────
    col1, col2 = st.columns([1, 3])
    
    with col1:
        max_rev = st.slider(
            "Max revisions",
            min_value=1,
            max_value=5,
            value=3,
            help="Maximum revision attempts if scores are below 7"
        )
    
    with col2:
        st.markdown("")
        st.markdown("")
        st.caption("💡 Reviewer scores: Tone, Persuasion, CTA, Grammar (each /10). Loop continues until all ≥7.")
    
    # ─── Run Button ────────────────────────────────────
    if st.button("🚀 Generate Email", type="primary", use_container_width=True):
        if not user_input.strip():
            st.warning("Please enter an email brief first.")
            return
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.info("✍️ Writer is drafting your email...")
        progress_bar.progress(20)
        
        try:
            # Run the multi-agent system
            result = agent.run(
                user_input=user_input,
                thread_id=f"email-{id(user_input)}",
                max_revisions=max_rev,
                email_type=email_type
            )
            
            progress_bar.progress(100)
            status_text.empty()
            
            # ─── Display Results ───────────────────────
            st.markdown("---")
            
            # Status badge
            if result["status"] == "approved":
                st.success(f"✅ Approved in {result['revisions']} revision(s)")
            else:
                st.warning(f"⚠️ Maxed out {result['revisions']} revision(s) — review manually")
            
            # ─── Final Email ───────────────────────────
            st.markdown("### 📨 Final Email")
            
            # Try to separate subject and body
            email_content = result["final_email"]
            if "SUBJECT:" in email_content.upper():
                # Split subject and body
                parts = email_content.split("\n", 2)
                if len(parts) >= 2:
                    subject_line = parts[0].replace("SUBJECT:", "").replace("Subject:", "").strip()
                    body = parts[2] if len(parts) > 2 else ""
                    
                    st.markdown(f"**Subject:** {subject_line}")
                    st.markdown("")
                    st.markdown(body)
                else:
                    st.markdown(email_content)
            else:
                st.markdown(email_content)
            
            # ─── Scores ────────────────────────────────
            st.markdown("---")
            st.markdown("### 📊 Final Scores")
            
            scores = result["scores"]
            cols = st.columns(4)
            
            score_colors = {
                "tone": "🟢" if scores["tone"] >= 8 else "🟡" if scores["tone"] >= 7 else "🔴",
                "persuasion": "🟢" if scores["persuasion"] >= 8 else "🟡" if scores["persuasion"] >= 7 else "🔴",
                "cta": "🟢" if scores["cta"] >= 8 else "🟡" if scores["cta"] >= 7 else "🔴",
                "grammar": "🟢" if scores["grammar"] >= 8 else "🟡" if scores["grammar"] >= 7 else "🔴",
            }
            
            cols[0].metric(f"{score_colors['tone']} Tone", f"{scores['tone']}/10")
            cols[1].metric(f"{score_colors['persuasion']} Persuasion", f"{scores['persuasion']}/10")
            cols[2].metric(f"{score_colors['cta']} CTA", f"{scores['cta']}/10")
            cols[3].metric(f"{score_colors['grammar']} Grammar", f"{scores['grammar']}/10")
            
            # ─── Revision History ──────────────────────
            if result["history"] and len(result["history"]) > 1:
                st.markdown("---")
                st.markdown("### 📝 Revision History")
                
                for item in result["history"]:
                    version = item["version"]
                    draft = item["draft"]
                    item_scores = item.get("scores")
                    feedback = item.get("feedback")
                    
                    with st.expander(f"Version {version}" + 
                                    (f" - Scores: {item_scores}" if item_scores else " (Initial draft)")):
                        
                        st.markdown(f"**Draft:**")
                        st.text(draft)
                        
                        if feedback:
                            st.markdown("")
                            st.markdown(f"**Reviewer Feedback:**")
                            st.text(feedback)
            
            # ─── Save to session state ─────────────────
            if "email_history" not in st.session_state:
                st.session_state.email_history = []
            
            st.session_state.email_history.append({
                "brief": user_input,
                "type": email_type,
                "email": result["final_email"],
                "scores": scores,
                "revisions": result["revisions"],
                "status": result["status"]
            })
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Error: {e}")
            st.exception(e)
    
    # ─── Tips Section ──────────────────────────────────
    st.markdown("---")
    with st.expander("💡 Tips for Better Emails"):
        st.markdown("""
        **For best results, include in your brief:**
        - **Audience**: Who is this email for? (new users, leads, customers)
        - **Goal**: What action should they take? (sign up, buy, reply)
        - **Tone**: Formal, casual, urgent, friendly?
        - **Key message**: Main thing they should remember
        - **Offer**: Any discount, free trial, or incentive?
        
        **Example good brief:**
        > "Welcome email for new SaaS signup. User just signed up for 14-day free trial. 
        > Goal: get them to complete their profile and invite a teammate. 
        > Tone: warm, helpful. Include 3 quick onboarding steps."
        """)
    
    # ─── History ───────────────────────────────────────
    if st.session_state.get("email_history"):
        st.markdown("---")
        st.markdown("### 📜 Recent Emails (this session)")
        
        for i, item in enumerate(reversed(st.session_state.email_history[-5:])):
            status_icon = "✅" if item["status"] == "approved" else "⚠️"
            with st.expander(f"{status_icon} {item['type']} — {item['brief'][:50]}..."):
                st.markdown(f"**Type:** {item['type']}")
                st.markdown(f"**Revisions:** {item['revisions']}")
                st.markdown(f"**Scores:** {item['scores']}")
                st.markdown("**Email:**")
                st.text(item["email"])