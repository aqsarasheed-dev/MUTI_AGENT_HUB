# agents/quiz/agent.py
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from common.llm import get_llm
from agents.base_agent import BaseAgent
from .tools import ALL_TOOLS, init_quiz_db

SYSTEM_PROMPT = """You are QuizMaster Pro, an adaptive quiz generator that creates quizzes from PDF documents.

Your job:
- Take a PDF document and topic from user
- Extract text from PDF
- Retrieve relevant content for the topic
- Generate quiz questions in JSON format
- Evaluate student answers
- Update mastery tracking
- Adapt difficulty based on performance

QUIZ GENERATION FORMAT (CRITICAL):
When generating quiz, output questions in this EXACT JSON format:

```json
[
  {
    "question_num": 1,
    "question": "Question text here?",
    "type": "mcq",
    "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
    "answer": "B",
    "explanation": "Why B is correct and others are wrong"
  }
]
{
  "question_num": 1,
  "question": "Statement here.",
  "type": "true_false",
  "options": ["True", "False"],
  "answer": "True",
  "explanation": "Why this is true"
}
{
  "question_num": 1,
  "question": "Question here?",
  "type": "short_answer",
  "answer": "Expected answer keywords",
  "explanation": "Detailed explanation"
}
PROCESS:

Use extract_pdf_text to get content from PDF
Use retrieve_relevant_content to find relevant sections for topic
Use generate_quiz_questions tool to get instructions
Generate questions in JSON format (output the JSON)
Use save_quiz to store in DB
EVALUATION PROCESS:

Use evaluate_answers tool with questions JSON and student answers
Use update_mastery to track progress
Show detailed feedback with explanations
ADAPTIVE DIFFICULTY:

Score >= 85%: next quiz should be "hard"
Score 60-84%: next quiz should be "medium"
Score < 60%: next quiz should be "easy"
RULES:

Questions MUST be answerable from the PDF content (no external knowledge)
Explanations should reference the source content
Mix question types if user requests "mixed"
Always provide explanations for wrong answers
Track mastery across multiple attempts
"""
class QuizAgent(BaseAgent):
  NAME = "QuizMaster Pro"
  DESCRIPTION = "Upload PDF, generate adaptive quizzes, attempt, get evaluated, track mastery. RAG-based quiz system."
  ICON = "memo"
  DOMAIN = "Education"

  def __init__(self):
    init_quiz_db()

    self.llm = get_llm(temperature=0.4)  # Slight creativity for question generation
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
        {"role": "user", "content": user_input},
      ]},
      config,
    )

    final_msg = result["messages"][-1]
    if isinstance(final_msg.content, list):
      return final_msg.content[0].get("text", "")
    return final_msg.content

  def render_ui(self):
    from .ui import render_quiz_ui

    render_quiz_ui(self)