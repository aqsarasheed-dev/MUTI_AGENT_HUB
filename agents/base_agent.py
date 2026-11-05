# agents/base_agent.py
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Every agent must extend this class."""
    
    NAME: str = "Unnamed Agent"
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