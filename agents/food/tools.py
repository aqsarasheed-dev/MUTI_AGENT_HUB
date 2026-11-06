# agents/food/tools.py
import sqlite3
import json
from langchain_core.tools import tool
from functools import lru_cache

# ─── Database Setup ─────────────────────────────────────
DB_PATH = "database/food.db"

@lru_cache(maxsize=1)
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_food_db():
    """Create tables and seed sample recipes. Run once."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            ingredients TEXT,
            instructions TEXT,
            calories INTEGER,
            protein_g REAL,
            carbs_g REAL,
            fat_g REAL,
            fiber_g REAL
        );
        
        CREATE TABLE IF NOT EXISTS substitutions (
            id INTEGER PRIMARY KEY,
            original TEXT NOT NULL,
            target_diet TEXT NOT NULL,
            substitute TEXT NOT NULL,
            reason TEXT,
            protein_change REAL,
            calories_change REAL
        );
        
        CREATE TABLE IF NOT EXISTS transformations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_recipe TEXT,
            target_diet TEXT,
            transformed_ingredients TEXT,
            transformed_nutrition TEXT,
            substitutions_used TEXT,
            reasoning TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # ─── Seed Recipes ───
    recipe_count = db.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
    if recipe_count == 0:
        recipes = [
            ("Chicken Biryani", "main",
             json.dumps([{"item": "Chicken", "qty": "300g"}, {"item": "Basmati Rice", "qty": "2 cups"}, {"item": "Yogurt", "qty": "1 cup"}, {"item": "Onions", "qty": "2"}, {"item": "Ghee", "qty": "3 tbsp"}, {"item": "Biryani Masala", "qty": "2 tbsp"}]),
             "Marinate chicken in yogurt + spices. Cook rice separately. Layer chicken and rice. Steam for 20 min.",
             650, 38, 65, 22, 3),
            
            ("Beef Burger", "main",
             json.dumps([{"item": "Beef Patty", "qty": "200g"}, {"item": "Burger Bun", "qty": "1"}, {"item": "Cheese Slice", "qty": "1"}, {"item": "Lettuce", "qty": "1 leaf"}, {"item": "Tomato", "qty": "2 slices"}, {"item": "Mayo", "qty": "2 tbsp"}]),
             "Grill beef patty 4 min each side. Toast bun. Add cheese, lettuce, tomato, mayo.",
             580, 32, 45, 28, 2),
            
            ("Caesar Salad", "salad",
             json.dumps([{"item": "Romaine Lettuce", "qty": "4 cups"}, {"item": "Chicken Breast", "qty": "150g"}, {"item": "Parmesan Cheese", "qty": "50g"}, {"item": "Croutons", "qty": "1 cup"}, {"item": "Caesar Dressing", "qty": "3 tbsp"}]),
             "Grill chicken. Chop lettuce. Toss with dressing. Top with chicken, cheese, croutons.",
             420, 35, 12, 25, 3),
            
            ("Pasta Carbonara", "main",
             json.dumps([{"item": "Spaghetti", "qty": "200g"}, {"item": "Bacon", "qty": "100g"}, {"item": "Eggs", "qty": "2"}, {"item": "Parmesan Cheese", "qty": "50g"}, {"item": "Black Pepper", "qty": "1 tsp"}]),
             "Cook pasta. Fry bacon. Mix eggs + cheese. Toss hot pasta with egg mixture + bacon.",
             580, 24, 68, 22, 3),
            
            ("Paneer Tikka", "main",
             json.dumps([{"item": "Paneer", "qty": "250g"}, {"item": "Yogurt", "qty": "100g"}, {"item": "Tikka Masala", "qty": "2 tbsp"}, {"item": "Bell Peppers", "qty": "2"}, {"item": "Onions", "qty": "1"}, {"item": "Lemon Juice", "qty": "1 tbsp"}]),
             "Marinate paneer in yogurt + spices. Skewer with veggies. Grill 15 min.",
             380, 22, 18, 24, 3),
            
            ("Greek Yogurt Bowl", "breakfast",
             json.dumps([{"item": "Greek Yogurt", "qty": "200g"}, {"item": "Honey", "qty": "2 tbsp"}, {"item": "Granola", "qty": "50g"}, {"item": "Berries", "qty": "50g"}, {"item": "Almonds", "qty": "20g"}]),
             "Layer yogurt, granola, berries. Drizzle honey. Top with almonds.",
             380, 20, 48, 12, 4),
            
            ("Avocado Toast", "breakfast",
             json.dumps([{"item": "Bread", "qty": "2 slices"}, {"item": "Avocado", "qty": "1"}, {"item": "Lemon Juice", "qty": "1 tsp"}, {"item": "Egg", "qty": "1"}, {"item": "Salt", "qty": "pinch"}, {"item": "Pepper", "qty": "pinch"}]),
             "Toast bread. Mash avocado with lemon. Top toast with avocado + fried egg.",
             340, 14, 32, 18, 8),
            
            ("Chicken Caesar Wrap", "main",
             json.dumps([{"item": "Tortilla", "qty": "1 large"}, {"item": "Chicken Breast", "qty": "150g"}, {"item": "Romaine", "qty": "1 cup"}, {"item": "Parmesan", "qty": "30g"}, {"item": "Caesar Dressing", "qty": "2 tbsp"}]),
             "Grill chicken. Lay tortilla. Add chicken, lettuce, cheese, dressing. Roll up.",
             480, 35, 38, 18, 3),
            
            ("Mango Lassi", "drink",
             json.dumps([{"item": "Yogurt", "qty": "1 cup"}, {"item": "Mango", "qty": "1"}, {"item": "Sugar", "qty": "2 tbsp"}, {"item": "Cardamom", "qty": "1/4 tsp"}, {"item": "Ice", "qty": "1 cup"}]),
             "Blend all ingredients until smooth. Serve chilled.",
             280, 8, 56, 4, 2),
            
            ("Vegetable Omelette", "breakfast",
             json.dumps([{"item": "Eggs", "qty": "3"}, {"item": "Bell Peppers", "qty": "1/2"}, {"item": "Onions", "qty": "1/4"}, {"item": "Cheese", "qty": "30g"}, {"item": "Salt", "qty": "pinch"}, {"item": "Pepper", "qty": "pinch"}]),
             "Whisk eggs. Saute veggies. Pour eggs, add cheese. Fold when set.",
             320, 24, 6, 22, 2),
        ]
        
        db.executemany(
            "INSERT INTO recipes (name, category, ingredients, instructions, calories, protein_g, carbs_g, fat_g, fiber_g) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            recipes
        )
    
    # ─── Seed Substitutions ───
    sub_count = db.execute("SELECT COUNT(*) FROM substitutions").fetchone()[0]
    if sub_count == 0:
        substitutions = [
            # Vegan substitutions
            ("Chicken", "vegan", "Chickpeas or Tofu", "Protein match (chickpea: 19g/cup), texture similar when marinated", -8, -50),
            ("Beef Patty", "vegan", "Black Bean Patty", "Protein (15g), iron-rich, similar texture when grilled", -10, -80),
            ("Cheese", "vegan", "Nutritional Yeast + Cashew Cream", "Cheesy flavor, B12 fortified, creamy texture", -5, -40),
            ("Yogurt", "vegan", "Coconut Yogurt", "Same creaminess, probiotics, dairy-free", -2, +20),
            ("Eggs", "vegan", "Flax Egg (1 tbsp flax + 3 tbsp water)", "Binding agent, omega-3, works in baking", -5, -60),
            ("Honey", "vegan", "Maple Syrup", "Same sweetness, vegan, minerals", 0, +10),
            ("Ghee", "vegan", "Coconut Oil", "Same fat content, vegan, high smoke point", 0, 0),
            ("Bacon", "vegan", "Smoked Tempeh", "Smoky flavor, protein (18g), crispy texture", -5, -70),
            
            # Keto substitutions
            ("Basmati Rice", "keto", "Cauliflower Rice", "Only 5g carbs vs 45g, similar texture", -2, -180),
            ("Burger Bun", "keto", "Lettuce Wrap", "Zero carbs, fresh crunch, holds patty well", -3, -40),
            ("Spaghetti", "keto", "Zucchini Noodles (Zoodles)", "Only 6g carbs vs 45g, low calorie", -2, -170),
            ("Bread", "keto", "Cloud Bread (cream cheese + eggs)", "Less than 1g carb per slice, fluffy", +2, -60),
            ("Tortilla", "keto", "Cheese Shell (Parmesan crisp)", "1g carb, high protein, crispy", +8, -20),
            ("Sugar", "keto", "Stevia or Erythritol", "Zero carbs, zero calories, sweet taste", 0, -16),
            ("Granola", "keto", "Nuts + Seeds Mix", "Low carb, high fat, crunchy", +4, -30),
            ("Croutons", "keto", "Pork Rinds", "Zero carbs, crispy, protein", +5, -10),
            
            # Gluten-free substitutions
            ("Burger Bun", "gluten-free", "GF Bun or Lettuce Wrap", "Same texture (GF bun) or low-carb (lettuce)", 0, -10),
            ("Spaghetti", "gluten-free", "Rice Noodles or Zoodles", "Rice noodles: same texture, GF certified", -1, -20),
            ("Bread", "gluten-free", "GF Bread (almond flour)", "Similar texture, almond flour base", +2, -5),
            ("Tortilla", "gluten-free", "Corn Tortilla", "Naturally GF, slightly different flavor", -1, -5),
            ("Crumbeled Croutons", "gluten-free", "GF Croutons or Nuts", "Same crunch, no gluten", +1, -10),
            
            # Low-carb substitutions
            ("Basmati Rice", "low-carb", "Cauliflower Rice", "5g vs 45g carbs, neutral taste", -2, -180),
            ("Spaghetti", "low-carb", "Zoodles", "6g vs 45g carbs, fresh", -2, -170),
            ("Sugar", "low-carb", "Monk Fruit Sweetener", "Zero carbs, zero calories, natural", 0, -16),
            ("Granola", "low-carb", "Nuts + Coconut", "5g vs 40g carbs per serving", +3, -50),
            ("Burger Bun", "low-carb", "Lettuce Wrap", "1g vs 30g carbs", -3, -40),
            
            # Diabetic-friendly substitutions
            ("Sugar", "diabetic", "Stevia or Cinnamon", "Zero glycemic impact, cinnamon helps blood sugar", 0, -16),
            ("White Rice", "diabetic", "Quinoa or Brown Rice", "Lower GI, more fiber, slower sugar release", +2, -20),
            ("White Bread", "diabetic", "Whole Grain Bread", "Lower GI, more fiber, complex carbs", +1, -5),
            ("Honey", "diabetic", "Stevia Drops", "Zero sugar, no blood spike", 0, -16),
            ("Mango", "diabetic", "Berries", "Lower sugar (5g vs 23g), high antioxidants", -1, -80),
            
            # Vegetarian substitutions
            ("Chicken", "vegetarian", "Paneer or Tofu", "Protein match, similar texture", -3, -50),
            ("Beef Patty", "vegetarian", "Veggie Patty (soy/mushroom)", "Protein (15g), meaty texture", -8, -60),
            ("Bacon", "vegetarian", "Mushroom Bacon", "Smoky, crispy, umami flavor", -10, -80),
        ]
        
        db.executemany(
            "INSERT INTO substitutions (original, target_diet, substitute, reason, protein_change, calories_change) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            substitutions
        )
    
    db.commit()


# ─── Tools ──────────────────────────────────────────────

@tool
def get_recipe_info(recipe_name: str) -> str:
    """Get base recipe information including ingredients and nutrition.
    
    Args:
        recipe_name: Name of the recipe (e.g., "Chicken Biryani", "Beef Burger")
    
    Returns:
        Formatted recipe with ingredients list, instructions, and nutrition.
    """
    db = get_db()
    row = db.execute(
        "SELECT * FROM recipes WHERE name LIKE ?",
        (f"%{recipe_name}%",)
    ).fetchone()
    
    if not row:
        return f"Recipe '{recipe_name}' not found. Try: Chicken Biryani, Beef Burger, Caesar Salad, Pasta Carbonara, Paneer Tikka, Greek Yogurt Bowl, Avocado Toast, Chicken Caesar Wrap, Mango Lassi, Vegetable Omelette"
    
    ingredients = json.loads(row["ingredients"])
    ing_list = "\n".join([f"  - {i['item']}: {i['qty']}" for i in ingredients])
    
    return (
        f"Recipe: {row['name']} (Category: {row['category']})\n\n"
        f"Ingredients:\n{ing_list}\n\n"
        f"Instructions: {row['instructions']}\n\n"
        f"Nutrition (per serving):\n"
        f"  Calories: {row['calories']}\n"
        f"  Protein: {row['protein_g']}g\n"
        f"  Carbs: {row['carbs_g']}g\n"
        f"  Fat: {row['fat_g']}g\n"
        f"  Fiber: {row['fiber_g']}g"
    )


@tool
def get_substitution(ingredient: str, target_diet: str) -> str:
    """Find a substitution for an ingredient to match target diet.
    
    Args:
        ingredient: Original ingredient name (e.g., "Chicken", "Cheese", "Sugar")
        target_diet: Target diet type (vegan, vegetarian, keto, gluten-free, low-carb, diabetic)
    
    Returns:
        Substitution with reasoning and nutrition impact.
    """
    db = get_db()
    row = db.execute(
        "SELECT * FROM substitutions WHERE original LIKE ? AND target_diet = ?",
        (f"%{ingredient}%", target_diet)
    ).fetchone()
    
    if not row:
        return f"No specific substitution found for '{ingredient}' → {target_diet}. Use general knowledge."
    
    return (
        f"Substitution for {row['original']} → {row['target_diet']}:\n"
        f"  Substitute: {row['substitute']}\n"
        f"  Reason: {row['reason']}\n"
        f"  Protein change: {row['protein_change']:+.0f}g\n"
        f"  Calories change: {row['calories_change']:+.0f}"
    )


@tool
def calculate_nutrition(ingredients_list: str, target_diet: str = "") -> str:
    """Calculate total nutrition for a list of ingredients.
    
    Args:
        ingredients_list: Comma-separated list of ingredients
        target_diet: Optional target diet for adjusted calculation
    
    Returns:
        Total calories, protein, carbs, fat for the ingredient list.
    """
    # Simplified nutrition lookup
    nutrition_db = {
        "chicken": {"cal": 165, "p": 31, "c": 0, "f": 3.6, "unit": "100g"},
        "beef": {"cal": 250, "p": 26, "c": 0, "f": 17, "unit": "100g"},
        "rice": {"cal": 130, "p": 2.7, "c": 28, "f": 0.3, "unit": "100g cooked"},
        "tofu": {"cal": 76, "p": 8, "c": 1.9, "f": 4.8, "unit": "100g"},
        "chickpeas": {"cal": 164, "p": 8.9, "c": 27, "f": 2.6, "unit": "100g"},
        "cheese": {"cal": 402, "p": 25, "c": 1.3, "f": 33, "unit": "100g"},
        "yogurt": {"cal": 59, "p": 10, "c": 3.6, "f": 0.4, "unit": "100g"},
        "eggs": {"cal": 155, "p": 13, "c": 1.1, "f": 11, "unit": "100g"},
        "sugar": {"cal": 387, "p": 0, "c": 100, "f": 0, "unit": "100g"},
        "honey": {"cal": 304, "p": 0.3, "c": 82, "f": 0, "unit": "100g"},
        "avocado": {"cal": 160, "p": 2, "c": 9, "f": 15, "unit": "100g"},
        "bread": {"cal": 265, "p": 9, "c": 49, "f": 3.2, "unit": "100g"},
        "pasta": {"cal": 158, "p": 6, "c": 31, "f": 0.9, "unit": "100g cooked"},
        "lettuce": {"cal": 15, "p": 1.4, "c": 2.9, "f": 0.2, "unit": "100g"},
        "cauliflower": {"cal": 25, "p": 1.9, "c": 5, "f": 0.3, "unit": "100g"},
    }
    
    ingredients = [i.strip().lower() for i in ingredients_list.split(",")]
    
    total_cal = 0
    total_p = 0
    total_c = 0
    total_f = 0
    
    found = []
    missing = []
    
    for ing in ingredients:
        matched = False
        for key, vals in nutrition_db.items():
            if key in ing:
                total_cal += vals["cal"]
                total_p += vals["p"]
                total_c += vals["c"]
                total_f += vals["f"]
                found.append(f"{ing} ({vals['cal']}cal)")
                matched = True
                break
        if not matched:
            missing.append(ing)
    
    result = (
        f"Nutrition for: {', '.join(found)}\n\n"
        f"Total (per 100g each):\n"
        f"  Calories: {total_cal}\n"
        f"  Protein: {total_p:.1f}g\n"
        f"  Carbs: {total_c:.1f}g\n"
        f"  Fat: {total_f:.1f}g\n"
    )
    
    if target_diet:
        result += f"\nTarget diet: {target_diet}\n"
        if target_diet == "keto" and total_c > 50:
            result += "⚠️ Carbs too high for keto (target < 50g/day)\n"
        elif target_diet == "low-carb" and total_c > 100:
            result += "⚠️ Carbs high for low-carb (target < 100g/day)\n"
    
    if missing:
        result += f"\nNot in DB (estimate manually): {', '.join(missing)}\n"
    
    return result


@tool
def save_transformation(
    original_recipe: str,
    target_diet: str,
    transformed_ingredients: str,
    transformed_nutrition: str,
    substitutions_used: str,
    reasoning: str
) -> str:
    """Save a recipe transformation to database for future reference.
    
    Args:
        original_recipe: Name of original recipe
        target_diet: Target diet type
        transformed_ingredients: Comma-separated new ingredients
        transformed_nutrition: New nutrition info
        substitutions_used: What was substituted
        reasoning: Why these substitutions were chosen
    """
    db = get_db()
    db.execute(
        """INSERT INTO transformations 
           (original_recipe, target_diet, transformed_ingredients, 
            transformed_nutrition, substitutions_used, reasoning)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (original_recipe, target_diet, transformed_ingredients,
         transformed_nutrition, substitutions_used, reasoning)
    )
    db.commit()
    return f"Transformation saved! Recipe: {original_recipe} → {target_diet}"


@tool
def get_transformation_history(limit: int = 5) -> str:
    """Get past recipe transformations for reference.
    
    Args:
        limit: Number of past transformations to retrieve (default 5)
    
    Returns:
        List of past transformations with original recipe, diet, and reasoning.
    """
    db = get_db()
    rows = db.execute(
        "SELECT * FROM transformations ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    
    if not rows:
        return "No past transformations yet."
    
    results = []
    for r in rows:
        results.append(
            f"ID: {r['id']} | {r['original_recipe']} → {r['target_diet']}\n"
            f"  Substitutions: {r['substitutions_used']}\n"
            f"  Reasoning: {r['reasoning']}\n"
            f"  Date: {r['created_at']}"
        )
    
    return "\n\n".join(results)


# ─── All Tools List ─────────────────────────────────────
ALL_TOOLS = [
    get_recipe_info,
    get_substitution,
    calculate_nutrition,
    save_transformation,
    get_transformation_history,
]