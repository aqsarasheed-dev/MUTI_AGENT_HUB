# agents/medical/tools.py
import sqlite3
from langchain_core.tools import tool
from functools import lru_cache

# ─── Database Setup ─────────────────────────────────────
DB_PATH = "database/medical.db"

@lru_cache(maxsize=1)
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_medical_db():
    """Create tables and seed medicine database."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            generic_name TEXT,
            category TEXT,
            description TEXT,
            otc INTEGER DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS drug_interactions (
            id INTEGER PRIMARY KEY,
            drug1 TEXT NOT NULL,
            drug2 TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT,
            action TEXT
        );
        
        CREATE TABLE IF NOT EXISTS food_interactions (
            id INTEGER PRIMARY KEY,
            medicine TEXT NOT NULL,
            food TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT
        );
        
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_medicines TEXT,
            new_medicine TEXT,
            interactions_found TEXT,
            recommendation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # ─── Seed Medicines ───
    med_count = db.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
    if med_count == 0:
        medicines = [
            # Painkillers / NSAIDs
            ("Panadol", "Paracetamol", "Analgesic", "Pain reliever and fever reducer", 1),
            ("Brufen", "Ibuprofen", "NSAID", "Anti-inflammatory painkiller", 1),
            ("Aspirin", "Acetylsalicylic acid", "NSAID", "Pain reliever and blood thinner", 1),
            ("Disprin", "Aspirin", "NSAID", "Pain reliever", 1),
            ("Naproxen", "Naproxen", "NSAID", "Anti-inflammatory painkiller", 1),
            ("Diclofenac", "Diclofenac sodium", "NSAID", "Strong anti-inflammatory", 0),
            ("Celebrex", "Celecoxib", "NSAID (COX-2)", "Anti-inflammatory with less GI effects", 0),
            
            # Antibiotics
            ("Augmentin", "Amoxicillin + Clavulanic acid", "Antibiotic", "Broad-spectrum antibiotic", 0),
            ("Amoxil", "Amoxicillin", "Antibiotic", "Penicillin-type antibiotic", 0),
            ("Ciprofloxacin", "Ciprofloxacin", "Antibiotic", "Fluoroquinolone antibiotic", 0),
            ("Flagyl", "Metronidazole", "Antibiotic", "For anaerobic infections", 0),
            ("Zithromax", "Azithromycin", "Antibiotic", "Macrolide antibiotic", 0),
            ("Klaricid", "Clarithromycin", "Antibiotic", "Macrolide antibiotic", 0),
            
            # Stomach / Acid
            ("Nexium", "Esomeprazole", "PPI", "Proton pump inhibitor for acid reflux", 0),
            ("Omeprazole", "Omeprazole", "PPI", "Reduces stomach acid", 1),
            ("Pepcid", "Famotidine", "H2 Blocker", "Reduces stomach acid", 1),
            ("Gaviscon", "Sodium alginate", "Antacid", "For heartburn", 1),
            ("Motilium", "Domperidone", "Antiemetic", "For nausea and vomiting", 0),
            
            # Diabetes
            ("Glucophage", "Metformin", "Antidiabetic", "For type 2 diabetes", 0),
            ("Januvia", "Sitagliptin", "Antidiabetic", "DPP-4 inhibitor", 0),
            ("Lantus", "Insulin glargine", "Insulin", "Long-acting insulin", 0),
            
            # Blood Pressure / Heart
            ("Tenormin", "Atenolol", "Beta-blocker", "For high BP and heart", 0),
            ("Lopressor", "Metoprolol", "Beta-blocker", "For heart conditions", 0),
            ("Norvasc", "Amlodipine", "Calcium channel blocker", "For high BP", 0),
            ("Lasix", "Furosemide", "Diuretic", "Water pill for BP and edema", 0),
            ("Capoten", "Captopril", "ACE inhibitor", "For high BP", 0),
            
            # Cholesterol
            ("Lipitor", "Atorvastatin", "Statin", "Lowers cholesterol", 0),
            ("Crestor", "Rosuvastatin", "Statin", "Lowers cholesterol", 0),
            
            # Mental Health
            ("Prozac", "Fluoxetine", "SSRI", "Antidepressant", 0),
            ("Zoloft", "Sertraline", "SSRI", "Antidepressant", 0),
            ("Xanax", "Alprazolam", "Benzodiazepine", "For anxiety", 0),
            ("Valium", "Diazepam", "Benzodiazepine", "For anxiety and seizures", 0),
            
            # Allergy / Cold
            ("Zyrtec", "Cetirizine", "Antihistamine", "For allergies", 1),
            ("Claritin", "Loratadine", "Antihistamine", "Non-drowsy allergy medicine", 1),
            ("Benadryl", "Diphenhydramine", "Antihistamine", "For allergies and sleep", 1),
            ("Sudafed", "Pseudoephedrine", "Decongestant", "For nasal congestion", 1),
            
            # Thyroid
            ("Synthroid", "Levothyroxine", "Thyroid hormone", "For hypothyroidism", 0),
            
            # Blood thinner
            ("Warfarin", "Warfarin", "Anticoagulant", "Blood thinner", 0),
            
            # Steroids
            ("Prednisolone", "Prednisolone", "Corticosteroid", "Anti-inflammatory steroid", 0),
        ]
        db.executemany(
            "INSERT INTO medicines (name, generic_name, category, description, otc) VALUES (?, ?, ?, ?, ?)",
            medicines
        )
    
    # ─── Seed Drug-Drug Interactions ───
    inter_count = db.execute("SELECT COUNT(*) FROM drug_interactions").fetchone()[0]
    if inter_count == 0:
        interactions = [
            # Severe interactions
            ("Warfarin", "Aspirin", "SEVERE", "Both are blood thinners - significantly increased bleeding risk", "AVOID combination. Consult doctor immediately."),
            ("Warfarin", "Ibuprofen", "SEVERE", "NSAIDs increase bleeding risk with warfarin", "AVOID. Use Paracetamol instead for pain."),
            ("Warfarin", "Naproxen", "SEVERE", "Increased bleeding risk", "AVOID combination."),
            ("Warfarin", "Diclofenac", "SEVERE", "Increased bleeding risk", "AVOID combination."),
            
            ("Ciprofloxacin", "Warfarin", "SEVERE", "Ciprofloxacin increases warfarin effect", "Monitor INR closely or change antibiotic."),
            
            # Moderate interactions
            ("Ibuprofen", "Aspirin", "MODERATE", "Ibuprofen can reduce aspirin's heart-protective effect", "Take aspirin 30 min before ibuprofen."),
            ("Ibuprofen", "Diclofenac", "MODERATE", "Two NSAIDs together - increased GI side effects", "Avoid taking two NSAIDs. Use one only."),
            ("Naproxen", "Ibuprofen", "MODERATE", "Two NSAIDs together - increased stomach ulcer risk", "Use only one NSAID at a time."),
            ("Aspirin", "Ibuprofen", "MODERATE", "Increased GI bleeding risk", "Take with food. Monitor for stomach pain."),
            
            # Antibiotic interactions
            ("Augmentin", "Ibuprofen", "MODERATE", "May increase GI side effects", "Take antibiotic with food."),
            ("Amoxicillin", "Metformin", "MODERATE", "May affect blood sugar control", "Monitor blood sugar more frequently."),
            ("Ciprofloxacin", "Metformin", "MODERATE", "May affect blood sugar", "Monitor glucose levels."),
            
            # BP medicines
            ("Atenolol", "Ibuprofen", "MODERATE", "NSAIDs can reduce BP medicine effectiveness", "Monitor BP. Consider Paracetamol instead."),
            ("Lisinopril", "Ibuprofen", "MODERATE", "NSAIDs reduce ACE inhibitor effect", "Monitor BP. Use Paracetamol if possible."),
            ("Atenolol", "Metoprolol", "MODERATE", "Two beta-blockers - risk of slow heart rate", "Never combine two beta-blockers."),
            
            # Mental health
            ("Fluoxetine", "Sertraline", "SEVERE", "Two SSRIs - risk of serotonin syndrome", "AVOID combining SSRIs."),
            ("Fluoxetine", "Tramadol", "SEVERE", "Risk of serotonin syndrome", "AVOID combination."),
            ("Xanax", "Diazepam", "SEVERE", "Two benzodiazepines - excessive sedation", "AVOID combining."),
            ("Zoloft", "Xanax", "MODERATE", "Increased sedation and dizziness", "Use with caution. Avoid driving."),
            
            # Statins
            ("Atorvastatin", "Clarithromycin", "SEVERE", "Increases statin levels - muscle toxicity risk", "Avoid or reduce statin dose temporarily."),
            ("Simvastatin", "Ciprofloxacin", "SEVERE", "Increases statin levels - muscle damage risk", "Pause statin during antibiotic course."),
            
            # Thyroid
            ("Levothyroxine", "Iron supplements", "MODERATE", "Iron reduces levothyroxine absorption", "Take 4 hours apart."),
            ("Levothyroxine", "Calcium", "MODERATE", "Calcium reduces absorption", "Take 4 hours apart."),
            
            # Diabetes
            ("Metformin", "Ciprofloxacin", "MODERATE", "May cause low or high blood sugar", "Monitor glucose closely."),
            ("Metformin", "Furosemide", "MODERATE", "May affect kidney function", "Monitor kidney function."),
            
            # Steroids
            ("Prednisolone", "Ibuprofen", "MODERATE", "Increased stomach ulcer risk", "Take with PPI (omeprazole) for protection."),
            
            # Safe combinations
            ("Paracetamol", "Ibuprofen", "SAFE", "Often used together for pain", "Safe to combine. Alternate every 3 hours for fever."),
            ("Paracetamol", "Amoxicillin", "SAFE", "No interaction", "Safe to take together."),
            ("Paracetamol", "Augmentin", "SAFE", "No interaction", "Safe to take together."),
            ("Paracetamol", "Metformin", "SAFE", "No interaction", "Safe."),
            ("Cetirizine", "Paracetamol", "SAFE", "No interaction", "Safe for cold/flu treatment."),
            ("Cetirizine", "Amoxicillin", "SAFE", "No interaction", "Safe."),
        ]
        db.executemany(
            "INSERT INTO drug_interactions (drug1, drug2, severity, description, action) VALUES (?, ?, ?, ?, ?)",
            interactions
        )
    
    # ─── Seed Food Interactions ───
    food_count = db.execute("SELECT COUNT(*) FROM food_interactions").fetchone()[0]
    if food_count == 0:
        food_interactions = [
            # Severe food interactions
            ("Warfarin", "Grapefruit", "SEVERE", "Grapefruit significantly increases warfarin levels - bleeding risk"),
            ("Warfarin", "Spinach (Vitamin K)", "MODERATE", "Vitamin K reduces warfarin effect. Maintain consistent intake."),
            ("Warfarin", "Garlic supplements", "MODERATE", "Increased bleeding risk"),
            
            # Statins
            ("Atorvastatin", "Grapefruit", "SEVERE", "Grapefruit increases statin levels - muscle damage risk"),
            ("Simvastatin", "Grapefruit", "SEVERE", "Grapefruit significantly increases statin levels"),
            ("Rosuvastatin", "Grapefruit", "MODERATE", "Mild increase in statin levels"),
            
            # Antibiotics
            ("Ciprofloxacin", "Dairy products", "MODERATE", "Calcium reduces absorption. Take 2 hours apart."),
            ("Tetracycline", "Dairy products", "SEVERE", "Calcium significantly reduces absorption"),
            ("Amoxicillin", "Alcohol", "MODERATE", "Alcohol reduces antibiotic effectiveness"),
            ("Metronidazole", "Alcohol", "SEVERE", "SEVERE reaction - nausea, vomiting, headache. AVOID alcohol completely."),
            ("Cephalosporins", "Alcohol", "SEVERE", "Disulfiram-like reaction. Avoid alcohol."),
            
            # BP medicines
            ("Atenolol", "Alcohol", "MODERATE", "Increased dizziness and low BP"),
            ("Amlodipine", "Grapefruit", "MODERATE", "Increases medicine levels - risk of low BP"),
            
            # Diabetes
            ("Metformin", "Alcohol", "MODERATE", "Increased lactic acidosis risk. Limit alcohol."),
            ("Glipizide", "Alcohol", "MODERATE", "May cause low blood sugar"),
            
            # General
            ("Ibuprofen", "Alcohol", "MODERATE", "Increased stomach bleeding risk"),
            ("Aspirin", "Alcohol", "MODERATE", "Increased stomach bleeding risk"),
            ("Paracetamol", "Alcohol", "SEVERE", "SEVERE liver damage risk. Avoid alcohol completely."),
            
            # Thyroid
            ("Levothyroxine", "Soy products", "MODERATE", "Soy reduces absorption. Take 4 hours apart."),
            ("Levothyroxine", "Coffee/Espresso", "MODERATE", "Reduces absorption. Take with water only."),
            
            # Antacids
            ("Omeprazole", "Acidic foods", "MILD", "May reduce effectiveness"),
        ]
        db.executemany(
            "INSERT INTO food_interactions (medicine, food, severity, description) VALUES (?, ?, ?, ?)",
            food_interactions
        )
    
    db.commit()


# ─── Tools ──────────────────────────────────────────────

@tool
def get_medicine_info(medicine_name: str) -> str:
    """Get information about a medicine.
    
    Args:
        medicine_name: Brand or generic name (e.g., "Panadol", "Brufen", "Augmentin")
    
    Returns:
        Medicine details including generic name, category, and OTC status.
    """
    db = get_db()
    row = db.execute(
        "SELECT * FROM medicines WHERE name LIKE ? OR generic_name LIKE ?",
        (f"%{medicine_name}%", f"%{medicine_name}%")
    ).fetchone()
    
    if not row:
        return f"Medicine '{medicine_name}' not found in database. Consult a pharmacist."
    
    otc_status = "OTC (Over-the-counter)" if row["otc"] else "Prescription only"
    
    return (
        f"Medicine: {row['name']}\n"
        f"  Generic name: {row['generic_name']}\n"
        f"  Category: {row['category']}\n"
        f"  Status: {otc_status}\n"
        f"  Description: {row['description']}"
    )


@tool
def check_drug_interactions(medicines_list: str) -> str:
    """Check interactions between multiple medicines.
    
    Args:
        medicines_list: Comma-separated list of medicine names (e.g., "Brufen, Panadol, Warfarin")
    
    Returns:
        All drug-drug interactions found, with severity and recommended action.
    """
    db = get_db()
    meds = [m.strip() for m in medicines_list.split(",")] # Split the input string by commas and strip any whitespace
    
    all_interactions = []
    
    # Check all pairs of medicines for interactions
    for i, med1 in enumerate(meds): 
        for j, med2 in enumerate(meds):
            if i >= j: # Skip checking the same pair twice
                continue
            
            # Find in DB (check both directions)
            row = db.execute(
                "SELECT * FROM drug_interactions WHERE (drug1 LIKE ? AND drug2 LIKE ?) OR (drug1 LIKE ? AND drug2 LIKE ?)",
                (f"%{med1}%", f"%{med2}%", f"%{med2}%", f"%{med1}%")
            ).fetchall() # Fetch all rows that match the query
            
            for r in row:
                all_interactions.append({
                    "drugs": f"{med1} + {med2}",
                    "severity": r["severity"],
                    "description": r["description"],
                    "action": r["action"]
                })
    
    if not all_interactions:
        return f"No known interactions found between: {', '.join(meds)}\n\nNote: This database covers common interactions. Always consult a pharmacist for complete check."
    
    # Sort by severity
    severity_order = {"SEVERE": 0, "MODERATE": 1, "MILD": 2, "SAFE": 3}
    all_interactions.sort(key=lambda x: severity_order.get(x["severity"], 4)) # Sort interactions by severity using a predefined order (SEVERE first, then MODERATE, MILD, SAFE)
    
    result = f"DRUG INTERACTIONS FOUND: {len(all_interactions)}\n\n"
    
    for inter in all_interactions:
        emoji = "🔴" if inter["severity"] == "SEVERE" else "🟡" if inter["severity"] == "MODERATE" else "🟢" if inter["severity"] == "SAFE" else "⚪"
        result += f"{emoji} {inter['severity']}: {inter['drugs']}\n"
        result += f"   Effect: {inter['description']}\n"
        result += f"   Action: {inter['action']}\n\n"
    
    return result


@tool
def check_food_interactions(medicine_name: str) -> str:
    """Check food interactions for a specific medicine.
    
    Args:
        medicine_name: Medicine name (e.g., "Warfarin", "Augmentin", "Paracetamol")
    
    Returns:
        List of foods to avoid or take precautions with.
    """
    db = get_db()
    rows = db.execute(
        "SELECT * FROM food_interactions WHERE medicine LIKE ?",
        (f"%{medicine_name}%",)
    ).fetchall()
    
    if not rows:
        return f"No known food interactions for '{medicine_name}'."
    
    # Sort by severity 
    severity_order = {"SEVERE": 0, "MODERATE": 1, "MILD": 2}
    rows_list = sorted(rows, key=lambda x: severity_order.get(x["severity"], 3)) 
    
    result = f"FOOD INTERACTIONS for {medicine_name}:\n\n"
    
    for r in rows_list: 
        emoji = "🔴" if r["severity"] == "SEVERE" else "🟡" if r["severity"] == "MODERATE" else "🟢" 
        result += f"{emoji} {r['severity']}: {r['food']}\n"
        result += f"   {r['description']}\n\n"
    
    return result


@tool
def find_alternative(medicine_name: str, category: str = "") -> str:
    """Find alternative medicines in the same category.
    
    Args:
        medicine_name: Current medicine name
        category: Optional category filter (e.g., "NSAID", "Antibiotic")
    
    Returns:
        List of alternative medicines in the same category.
    """
    db = get_db()
    
    # Get current medicine's category
    if not category:
        med = db.execute(
            "SELECT category FROM medicines WHERE name LIKE ? OR generic_name LIKE ?",
            (f"%{medicine_name}%", f"%{medicine_name}%")
        ).fetchone()
        
        if not med:
            return f"Cannot find category for '{medicine_name}'"
        
        category = med["category"]
    
    # Find alternatives
    rows = db.execute(
        "SELECT * FROM medicines WHERE category = ? AND name NOT LIKE ?",
        (category, f"%{medicine_name}%")
    ).fetchall()
    
    if not rows:
        return f"No alternatives found in {category} category."
    
    result = f"ALTERNATIVES in {category} category:\n\n"
    
    for r in rows:
        otc_tag = "(OTC)" if r["otc"] else "(Prescription)"
        result += f"• {r['name']} {otc_tag}\n"
        result += f"  Generic: {r['generic_name']}\n"
        result += f"  Description: {r['description']}\n\n"
    
    result += "⚠️ Always consult doctor before switching medicines."
    return result


@tool
def save_consultation(user_medicines: str, new_medicine: str, interactions: str, recommendation: str) -> str:
    """Save consultation to database for record keeping.
    
    Args:
        user_medicines: Current medicines list
        new_medicine: New medicine being checked
        interactions: Interactions found
        recommendation: Final recommendation
    """
    db = get_db()
    db.execute(
        "INSERT INTO consultations (user_medicines, new_medicine, interactions_found, recommendation) VALUES (?, ?, ?, ?)",
        (user_medicines, new_medicine, interactions, recommendation)
    )
    db.commit()
    return "Consultation saved to records."


@tool
def get_consultation_history(limit: int = 5) -> str:
    """Get past consultations for reference.
    
    Args:
        limit: Number of past consultations (default 5)
    """
    db = get_db()
    rows = db.execute(
        "SELECT * FROM consultations ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    
    if not rows:
        return "No past consultations."
    
    results = []
    for r in rows:
        results.append(
            f"ID: {r['id']}\n"
            f"  Current Meds: {r['user_medicines']}\n"
            f"  New Medicine: {r['new_medicine']}\n"
            f"  Date: {r['created_at']}"
        )
    
    return "\n\n".join(results)


# ─── All Tools List ─────────────────────────────────────
ALL_TOOLS = [
    get_medicine_info,
    check_drug_interactions,
    check_food_interactions,
    find_alternative,
    save_consultation,
    get_consultation_history,
]