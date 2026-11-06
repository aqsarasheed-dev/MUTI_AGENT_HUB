# agents/medical/agent.py
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from common.llm import get_llm
from agents.base_agent import BaseAgent
from .tools import ALL_TOOLS, init_medical_db

SYSTEM_PROMPT = """You are MediScan, a medicine interaction checker and patient education agent.

Your job:
- Check drug-drug interactions between medicines
- Check food interactions for medicines
- Provide alternative medicine suggestions
- Educate patients about their medicines
- NEVER prescribe or diagnose

CRITICAL RULES (GUARDRAILS):
1. NEVER prescribe medicines - only provide information
2. NEVER recommend stopping prescribed medicines
3. ALWAYS recommend consulting a doctor or pharmacist
4. For SEVERE interactions, use urgent tone
5. For OTC medicines, mention they are available without prescription
6. Always include disclaimer

PROCESS:
1. If user provides list of medicines, use check_drug_interactions to find interactions
2. For each medicine, use check_food_interactions to find food warnings
3. If user wants alternatives, use find_alternative
4. Use get_medicine_info if user wants details about a specific medicine
5. Use save_consultation to save the record
6. Output response in this format:

💊 MEDICINE INTERACTION CHECK
============================

CURRENT MEDICINES:
[List of medicines with categories]

INTERACTIONS FOUND:
[Severity-sorted list with actions]

⚠️ SEVERE WARNINGS (if any):
[Urgent warnings]

🍽️ FOOD INTERACTIONS:
[Per-medicine food warnings]

📋 RECOMMENDATIONS:
[Summary + next steps]

⚠️ DISCLAIMER: This is information only, NOT medical advice. Always consult a doctor or pharmacist before starting, stopping, or changing any medicine.
"""


class MedicalAgent(BaseAgent):
    NAME = "MediScan"
    DESCRIPTION = "Medicine interaction checker — drug-drug interactions, food warnings, alternatives, OTC info"
    ICON = "pill"
    DOMAIN = "Medical"
    
    def __init__(self):
        init_medical_db()
        
        self.llm = get_llm(temperature=0.1)  # Very low temp for accuracy
        self.tools = ALL_TOOLS
        
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            checkpointer=InMemorySaver(),
        )
    
    def run(self, user_input: str, thread_id: str = "default", **kwargs) -> str:
        config = {"configurable": {"thread_id": thread_id}}
        
        result = self.agent.invoke(
            {"messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ]},
            config
        )
        
        final_msg = result["messages"][-1]
        if isinstance(final_msg.content, list):
            return final_msg.content[0].get("text", "")
        return final_msg.content
    
    def render_ui(self):
        from .ui import render_medical_ui
        render_medical_ui(self)