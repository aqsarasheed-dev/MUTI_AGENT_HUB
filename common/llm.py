# common/llm.py
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from functools import lru_cache

load_dotenv()

@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.3) -> ChatGroq:
    """Single LLM instance — reused by all agents."""
    return ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=temperature
    )