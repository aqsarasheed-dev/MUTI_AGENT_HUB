# agents/researcher/agent.py
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from common.llm import get_llm
from agents.base_agent import BaseAgent
from .tools import ALL_TOOLS

SYSTEM_PROMPT = """You are a Researcher Assistant specialized in news summarization 
and financial data analysis.

Your job:
- Search for recent news on user's query using Tavily
- Summarize key points in clear, concise format
- If user asks about stocks, use get_stock_price tool
- If user asks about investment gains, use calculate_gain tool
- Always cite sources (URLs) from search results
- Be factual, no hallucination

Output format:
Summary:
[2-3 sentence summary]

Key Points:
- Point 1
- Point 2
- Point 3

Stock Data: (if applicable)
[Price/gain info]

Sources:
- [URL 1]
- [URL 2]
"""


class ResearcherAgent(BaseAgent):
    NAME = "News Researcher"
    DESCRIPTION = "Search news, summarize, fetch stock prices, calculate gains"
    ICON = "search"
    DOMAIN = "Research"
    
    def __init__(self):
        self.llm = get_llm(temperature=0.2)
        self.tools = ALL_TOOLS
        
        # Removed 'prompt' parameter
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            checkpointer=InMemorySaver(),
        )
    
    def run(self, user_input: str, thread_id: str = "default", **kwargs) -> str:
        config = {"configurable": {"thread_id": thread_id}}
        
        # System message goes into messages list
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
        from .ui import render_researcher_ui
        render_researcher_ui(self)