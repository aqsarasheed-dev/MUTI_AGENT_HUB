# agents/food/ui.py
import streamlit as st

def render_food_ui(agent):
    """Streamlit UI for RecipeGenie agent."""
    
    st.markdown("### 🍲 Recipe to Diet Transformer")
    st.markdown("Transform any recipe to your target diet with smart substitutions + nutrition comparison.")
    
    # ─── Diet Selector ─────────────────────────────────
    diet_options = {
        "Vegan": "vegan",
        "Vegetarian": "vegetarian",
        "Keto": "keto",
        "Gluten-Free": "gluten-free",
        "Low-Carb": "low-carb",
        "Diabetic-Friendly": "diabetic"
    }
    
    selected_diet_label = st.selectbox(
        "🎯 Target Diet",
        list(diet_options.keys()),
        help="Select the diet you want to transform your recipe to"
    )
    selected_diet = diet_options[selected_diet_label]
    
    # ─── Recipe Input ──────────────────────────────────
    st.markdown("**Choose input method:**")
    input_method = st.radio(
        "Input method",
        ["Select from recipes", "Type custom recipe"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if input_method == "Select from recipes":
        # Quick recipe selector
        recipe_options = [
            "Chicken Biryani", "Beef Burger", "Caesar Salad", 
            "Pasta Carbonara", "Paneer Tikka", "Greek Yogurt Bowl",
            "Avocado Toast", "Chicken Caesar Wrap", "Mango Lassi",
            "Vegetable Omelette"
        ]
        selected_recipe = st.selectbox("📋 Choose recipe", recipe_options)
        
        # Optional custom modifications
        custom_mods = st.text_input(
            "Custom modifications (optional):",
            placeholder="e.g., extra spicy, no onions, low sodium"
        )
        
        if custom_mods:
            user_input = f"Transform '{selected_recipe}' to {selected_diet} diet. Modifications: {custom_mods}"
        else:
            user_input = f"Transform '{selected_recipe}' to {selected_diet} diet."
    
    else:
        # Custom recipe input
        recipe_name = st.text_input(
            "Recipe name:",
            placeholder="e.g., My Grandma's Chicken Curry"
        )
        
        ingredients = st.text_area(
            "Ingredients (one per line):",
            placeholder="Chicken 500g\nOnions 2\nYogurt 1 cup\nSpices 2 tbsp",
            height=120
        )
        
        instructions = st.text_area(
            "Instructions (optional):",
            placeholder="Marinate chicken. Cook onions. Add spices. Simmer 30 min.",
            height=80
        )
        
        if not recipe_name or not ingredients:
            user_input = ""
        else:
            user_input = (
                f"Transform this custom recipe to {selected_diet} diet.\n\n"
                f"Recipe: {recipe_name}\n"
                f"Ingredients:\n{ingredients}\n"
            )
            if instructions:
                user_input += f"Instructions: {instructions}"
    
    # ─── Diet Info Box ─────────────────────────────────
    with st.expander("ℹ️ About this diet"):
        diet_info = {
            "Vegan": "No animal products (no meat, dairy, eggs, honey). Plant-based only.",
            "Vegetarian": "No meat, but dairy and eggs allowed.",
            "Keto": "High fat, very low carb (<50g/day), moderate protein. Forces ketosis.",
            "Gluten-Free": "No wheat, barley, rye. For celiac disease or gluten sensitivity.",
            "Low-Carb": "Reduced carbs (50-100g/day), higher protein and fat.",
            "Diabetic-Friendly": "Low glycemic index, controlled carbs, no added sugar."
        }
        st.write(diet_info.get(selected_diet_label, ""))
    
    # ─── Run Button ────────────────────────────────────
    if st.button("🔄 Transform Recipe", type="primary", use_container_width=True):
        if not user_input.strip():
            st.warning("Please select or enter a recipe first.")
            return
        
        with st.spinner(f"Transforming to {selected_diet_label} diet..."):
            try:
                response = agent.run(
                    user_input, 
                    thread_id=f"food-{selected_diet}-{hash(user_input) % 10000}"
                )
                
                st.markdown("---")
                st.markdown("### 🍽️ Transformed Recipe")
                st.markdown(response)
                
                # Save to history
                if "food_history" not in st.session_state:
                    st.session_state.food_history = []
                
                st.session_state.food_history.append({
                    "recipe": recipe_name if input_method == "Type custom recipe" else selected_recipe,
                    "diet": selected_diet_label,
                    "response": response
                })
                
            except Exception as e:
                st.error(f"Error: {e}")
    
    # ─── Quick Examples ────────────────────────────────
    st.markdown("---")
    st.markdown("### 💡 Quick Examples")
    
    examples = [
        ("🥬 Chicken Biryani → Vegan", "Transform 'Chicken Biryani' to vegan diet."),
        ("🥩 Beef Burger → Keto", "Transform 'Beef Burger' to keto diet."),
        ("🍝 Pasta Carbonara → Gluten-Free", "Transform 'Pasta Carbonara' to gluten-free diet."),
        ("🥗 Caesar Salad → Diabetic", "Transform 'Caesar Salad' to diabetic-friendly diet."),
        ("🥪 Avocado Toast → Low-Carb", "Transform 'Avocado Toast' to low-carb diet."),
    ]
    
    cols = st.columns(len(examples))
    for col, (label, prompt) in zip(cols, examples):
        if col.button(label, key=f"example_{label}"):
            st.session_state.food_quick_prompt = prompt
    
    # Handle quick prompt
    if "food_quick_prompt" in st.session_state:
        prompt = st.session_state.food_quick_prompt
        del st.session_state.food_quick_prompt
        
        with st.spinner("Transforming..."):
            try:
                response = agent.run(
                    prompt,
                    thread_id=f"food-quick-{hash(prompt) % 10000}"
                )
                
                st.markdown("---")
                st.markdown("### 🍽️ Transformed Recipe")
                st.markdown(response)
                
                if "food_history" not in st.session_state:
                    st.session_state.food_history = []
                
                st.session_state.food_history.append({
                    "recipe": prompt.split("'")[1] if "'" in prompt else "Custom",
                    "diet": selected_diet_label,
                    "response": response
                })
            except Exception as e:
                st.error(f"Error: {e}")
    
    # ─── History ───────────────────────────────────────
    if st.session_state.get("food_history"):
        st.markdown("---")
        st.markdown("### 📜 Recent Transformations")
        
        for i, item in enumerate(reversed(st.session_state.food_history[-5:])):
            with st.expander(f"{item['recipe']} → {item['diet']}"):
                st.markdown(item["response"])