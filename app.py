# app.py
import streamlit as st
from agents import AGENTS_REGISTRY

# Page config
st.set_page_config(
    page_title="Multi-Agent AI Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── SIDEBAR ───────────────────────────────────────────
st.sidebar.markdown("## 🤖 AI Agent Hub")

# Group agents by domain
agents_by_domain = {}
for name, agent in AGENTS_REGISTRY.items():
    domain = agent.DOMAIN
    if domain not in agents_by_domain:
        agents_by_domain[domain] = []
    agents_by_domain[domain].append((name, agent))

# Domain dropdown
selected_domain = st.sidebar.selectbox(
    "📁 Domain",
    list(agents_by_domain.keys())
)

# Agent dropdown (filtered)
domain_agents = agents_by_domain[selected_domain]
agent_labels = [f"{a.ICON} {a.NAME}" for _, a in domain_agents]
selected_idx = st.sidebar.selectbox(
    "🤖 Agent",
    range(len(agent_labels)),
    format_func=lambda i: agent_labels[i]
)

selected_agent = domain_agents[selected_idx][1]

# Agent info
with st.sidebar.expander("ℹ️ About this agent"):
    st.write(selected_agent.DESCRIPTION)

st.sidebar.markdown("---")
st.sidebar.markdown("💡 Built with LangChain + Streamlit")

# ─── MAIN CONTENT ──────────────────────────────────────
st.title(f"{selected_agent.ICON} {selected_agent.NAME}")
st.markdown(f"*{selected_agent.DESCRIPTION}*")
st.markdown("---")

# Render agent UI
selected_agent.render_ui()