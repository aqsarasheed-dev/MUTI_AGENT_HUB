# agents/base_agent.py
from abc import ABC, abstractmethod

# abstract method , aisa function jo child class lazmi implement kare
class BaseAgent(ABC):  #abstract base class for all agents
    """Every agent must extend this class."""
    
    NAME: str = "Unnamed Agent"  #Yeh default values hain. Har child class inko override karega (apni values dega):
    DESCRIPTION: str = ""
    ICON: str = "🤖"
    DOMAIN: str = "general"
    
    @abstractmethod
    def run(self, user_input: str, thread_id: str = "default", **kwargs):
        """Main agent execution. Returns response."""
        pass
    
    @abstractmethod
    def render_ui(self):
        """Render Streamlit UI for this agent."""
        pass