# agents/medical/ui.py
import streamlit as st

def render_medical_ui(agent):
    """Streamlit UI for MediScan agent."""
    
    st.markdown("### 💊 MediScan — Medicine Interaction Checker")
    st.markdown("Check drug-drug interactions, food warnings, and find alternatives.")
    
    # ─── Quick Action Buttons ──────────────────────────
    st.markdown("#### 🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💊 Common Painkillers"):
            st.session_state.med_quick = "Check interactions between: Panadol, Brufen, Aspirin"
    with col2:
        if st.button("🦠 Antibiotic + Painkiller"):
            st.session_state.med_quick = "I'm taking Augmentin and want to take Brufen for pain. Check interactions."
    with col3:
        if st.button("🩸 Blood Thinter Check"):
            st.session_state.med_quick = "I'm on Warfarin. Can I take Aspirin or Brufen for headache?"
    
    # ─── User Input ────────────────────────────────────
    default_text = ""
    if "med_quick" in st.session_state:
        default_text = st.session_state.med_quick
        del st.session_state.med_quick
    
    user_input = st.text_area(
        "Enter your medicines or question:",
        value=default_text,
        placeholder="e.g., I'm taking Brufen and Panadol, want to add Augmentin. Check all interactions.",
        height=100
    )
    
    # ─── Medicine Database Lookup ──────────────────────
    with st.expander("🔍 Look up a medicine"):
        med_name = st.text_input("Medicine name:", placeholder="e.g., Panadol, Augmentin")
        if st.button("Get Info"):
            if med_name.strip():
                with st.spinner("Looking up..."):
                    from agents.medical.tools import get_medicine_info
                    info = get_medicine_info.invoke({"medicine_name": med_name})
                    st.info(info)
    
    # ─── Run Button ────────────────────────────────────
    if st.button("🔍 Check Interactions", type="primary", use_container_width=True):
        if not user_input.strip():
            st.warning("Please enter your medicines or question.")
            return
        
        with st.spinner("Checking interactions..."):
            try:
                response = agent.run(
                    user_input,
                    thread_id=f"medical-{hash(user_input) % 10000}"
                )
                
                st.markdown("---")
                st.markdown("### 📋 Interaction Report")
                st.markdown(response)
                
                # Show disclaimer prominently
                st.error(
                    "⚠️ **MEDICAL DISCLAIMER:** This is information only, NOT medical advice. "
                    "Always consult a doctor or pharmacist before starting, stopping, or changing any medicine."
                )
                
                # Save to history
                if "medical_history" not in st.session_state:
                    st.session_state.medical_history = []
                
                st.session_state.medical_history.append({
                    "query": user_input,
                    "response": response
                })
                
            except Exception as e:
                st.error(f"Error: {e}")
    
    # ─── Common Interactions Reference ─────────────────
    st.markdown("---")
    st.markdown("### 📚 Common Dangerous Combinations")
    
    with st.expander("⚠️ View Severe Interactions"):
        st.markdown("""
        | Combination | Risk | Action |
        |---|---|---|
        | Warfarin + Aspirin | Severe bleeding | AVOID |
        | Warfarin + Brufen/Ibuprofen | Severe bleeding | AVOID |
        | Paracetamol + Alcohol | Liver damage | AVOID alcohol |
        | Metronidazole + Alcohol | Severe reaction | AVOID alcohol completely |
        | SSRI antidepressants (combined) | Serotonin syndrome | AVOID |
        | Statins + Grapefruit | Muscle damage | Limit grapefruit |
        | Tetracycline + Dairy | Reduced absorption | Take 2hrs apart |
        """)
    
    # ─── Food Interactions Quick Reference ─────────────
    with st.expander("🍽️ Common Food Interactions"):
        st.markdown("""
        | Medicine | Food/Drink | Effect |
        |---|---|---|
        | Warfarin | Grapefruit, Spinach | Bleeding risk / reduced effect |
        | Statins (Lipitor) | Grapefruit | Muscle damage risk |
        | Antibiotics | Alcohol | Reduced effectiveness |
        | Ciprofloxacin | Dairy products | Reduced absorption |
        | Levothyroxine | Soy, Coffee | Reduced absorption |
        | Metformin | Alcohol | Lactic acidosis risk |
        | Paracetamol | Alcohol | Liver damage |
        """)
    
    # ─── History ───────────────────────────────────────
    if st.session_state.get("medical_history"):
        st.markdown("---")
        st.markdown("### 📜 Recent Checks")
        
        for i, item in enumerate(reversed(st.session_state.medical_history[-5:])):
            with st.expander(f"Check {i+1}: {item['query'][:60]}..."):
                st.markdown(item["response"])