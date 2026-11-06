# agents/food/agent.py
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from common.llm import get_llm
from agents.base_agent import BaseAgent
from .tools import ALL_TOOLS, init_food_db

SYSTEM_PROMPT = """You are RecipeGenie, an expert diet transformation agent.

Your job:
- Take a recipe from user
- Transform it to a target diet (vegan, vegetarian, keto, gluten-free, low-carb, diabetic)
- Find substitutions for non-compliant ingredients
- Calculate new nutrition
- Provide substitution reasoning (WHY each substitution was chosen)
- Save transformation for future reference

Process:
1. Use get_recipe_info to fetch base recipe details
2. For each ingredient, use get_substitution to find diet-compliant substitute
3. Use calculate_nutrition to compute new macros
4. Use save_transformation to store the result
5. Output the transformation in this EXACT format:

RECIPE TRANSFORMATION
Original: [recipe name]
Target Diet: [diet type]

SUBSTITUTIONS:
- [original 1] → [substitute 1]
  Reason: [why this substitute]
  Nutrition change: [+/-X cal, +/-Y protein]

- [original 2] → [substitute 2]
  Reason: [why]
  Nutrition change: [...]

NEW INGREDIENTS:
- [list all ingredients after substitution]

NUTRITION CHANGE:
- Calories: [old] → [new] ([+/-change])
- Protein: [old]g → [new]g
- Carbs: [old]g → [new]g
- Fat: [old]g → [new]g

REASONING SUMMARY:
[2-3 sentences explaining overall transformation logic - why these substitutions 
work together, what nutritional goals are met, any trade-offs]

GROCERY LIST ADDITIONS:
- [items you need to buy that you might not have]

Guidelines:
- ALWAYS explain WHY each substitution was chosen (protein match, texture, taste, etc.)
- If no exact substitution in DB, use general culinary knowledge
- Be honest about trade-offs (e.g., "vegan version has less protein, add legumes")
- Calculate total nutrition before and after
- Mention if transformation is suitable for the target diet (e.g., "✓ Keto-compliant: <50g carbs")
"""


class FoodAgent(BaseAgent):
    NAME = "RecipeGenie"
    DESCRIPTION = "Transform any recipe to your diet - vegan, keto, gluten-free, low-carb, diabetic. Get substitutions with reasoning + nutrition comparison."
    ICON = "food"
    DOMAIN = "Food"
    
    def __init__(self):
        # Initialize DB on first run
        init_food_db()
        
        self.llm = get_llm(temperature=0.4)
        self.tools = ALL_TOOLS
        
        # NOTE: No 'prompt' parameter (LangChain 1.x)
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
        from .ui import render_food_ui
        render_food_ui(self)