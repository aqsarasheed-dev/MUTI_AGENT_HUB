# agents/ecommerce/tools.py
import sqlite3
import re
from langchain_core.tools import tool
from functools import lru_cache 

# ─── Database Setup ─────────────────────────────────────
DB_PATH = "database/ecommerce.db"

@lru_cache(maxsize=1) 
def get_db(): #db connection ko cache krta h, jisse ki hr bar new connection na bnaye.
    conn = sqlite3.connect(DB_PATH, check_same_thread=False) #check_same_thread=False means that the connection can be used by multiple threads.
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

def init_email_db():
    """Create tables and seed sample templates. Run once."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS email_templates (
            id INTEGER PRIMARY KEY,
            category TEXT NOT NULL,
            subject TEXT,
            body TEXT,
            avg_score REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brief TEXT,
            email_type TEXT,
            final_draft TEXT,
            tone_score INTEGER,
            persuasion_score INTEGER,
            cta_score INTEGER,
            grammar_score INTEGER,
            revision_count INTEGER,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Seed templates if empty
    count = db.execute("SELECT COUNT(*) FROM email_templates").fetchone()[0]
    if count == 0:
                templates = [
                        ("Welcome", 
                         "Welcome to {product}, {name}! Your free trial starts now",
                         "Hi {name},\n\nWelcome to {product}! We're thrilled to have you.\n\nYour 14-day free trial is now active. Here's what you can do in the first 5 minutes:\n\n- Complete your profile\n- Connect your first integration\n- Invite a teammate\n\n[Get Started Now ->]\n\nReply to this email if you need anything. We're here to help.\n\nBest,\nThe {product} Team",
                         9.0),
                        ("Sales",
                         "Quick question, {name}",
                         "Hi {name},\n\nI noticed your company is scaling fast - congrats on the recent funding round.\n\nCompanies like {similar_company} use {product} to cut their reporting time by 60%. I think it could do the same for you.\n\nWorth a 15-min chat next week?\n\n[Book a Call ->]\n\nBest,\n{sender_name}",
                         8.5),
                        ("Newsletter",
                         "This week in {industry}: 5 trends you missed",
                         "Hi {name},\n\nHere's what happened in {industry} this week:\n\n1. Trend one - quick summary\n2. Trend two - quick summary\n3. Trend three - quick summary\n\nRead the full breakdown on our blog.\n\n[Read More ->]\n\nSee you next week,\nThe {product} Team",
                         8.0),
                        ("Re-engagement",
                         "We miss you, {name} (50% off inside)",
                         "Hi {name},\n\nWe noticed you haven't logged in for 30 days. We miss you!\n\nHere's 50% off your next 3 months - no strings attached.\n\n[Claim My Discount ->]\n\nOffer expires in 48 hours.\n\nBest,\nThe {product} Team",
                         8.5),
                        ("Support",
                         "Re: Your support request - {ticket_id}",
                         "Hi {name},\n\nThanks for reaching out. I've looked into your issue with {issue}.\n\nHere's the fix:\n\n1. Step one\n2. Step two\n3. Step three\n\nIf this doesn't resolve it, just reply and I'll dig deeper.\n\nBest,\n{sender_name}\nSupport Team",
                         9.0),
                        ("Thank You",
                         "Thank you for your purchase, {name}!",
                         "Hi {name},\n\nThank you for your order #{order_id}! Your item(s) will ship within 24 hours.\n\nOrder summary:\n- {item}\n- Total: ${total}\n\nTrack your order here: [Track Order ->]\n\nQuestions? Reply to this email.\n\nBest,\nThe {product} Team",
                         9.5),
                        ("Abandoned Cart",
                         "{name}, your cart is waiting (and so is 10% off)",
                         "Hi {name},\n\nYou left something behind:\n\n- {item} - ${price}\n\nComplete your order in the next 24 hours and get 10% off with code CART10.\n\n[Complete My Order ->]\n\nBest,\nThe {product} Team",
                         8.0),
                ]
                db.executemany(
            "INSERT INTO email_templates (category, subject, body, avg_score) VALUES (?, ?, ?, ?)",
            templates
        )
    
    db.commit()


# ─── Spam Words List ────────────────────────────────────
SPAM_TRIGGER_WORDS = [
    "free", "guarantee", "act now", "urgent", "limited time", "click here",
    "buy now", "cash", "credit", "loan", "make money", "100%", "best price",
    "winner", "congratulations", "risk-free", "no obligation", "exclusive deal",
    "miracle", "amazing", "incredible", "extra income", "double your",
    "$$$", "!!!"
]


# ─── Tools ──────────────────────────────────────────────

@tool
def get_email_templates(category: str = "") -> str: #DB SY email templates ko fetch krta h, agar category empty h to sb templates return krta h.
    """Get sample email templates for inspiration. Optionally filter by category.
    
    Args:
        category: Email type (Welcome, Sales, Newsletter, Re-engagement, Support, Thank You, Abandoned Cart)
                  Empty string returns all templates.
    
    Returns:
        Formatted list of templates with subject and body.
    """
    db = get_db() 
    
    if category:
        rows = db.execute( 
            "SELECT * FROM email_templates WHERE category = ? ORDER BY avg_score DESC",
            (category,)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM email_templates ORDER BY avg_score DESC"
        ).fetchall()
    
    if not rows:
        return f"No templates found for category: {category}" 
    #data format k liy loop 
    results = [] 
    for r in rows:
        results.append(
            f"--- Template ID: {r['id']} | Category: {r['category']} | Score: {r['avg_score']}/10 ---\n"
            f"Subject: {r['subject']}\n\n"
            f"Body:\n{r['body']}\n"
        )
    
    return "\n".join(results)


@tool
def check_spam_score(content: str) -> str:
    """Check email content for spam trigger words.
    
    Args:
        content: Email subject + body to check
    
    Returns:
        Spam risk assessment with list of trigger words found.
    """
    content_lower = content.lower()
    
    found = []
    
    for word in SPAM_TRIGGER_WORDS:
        if word in content_lower:
            found.append(word)
    
    if not found:
        return "Spam Risk: LOW - No trigger words detected."
    
    risk_level = "HIGH" if len(found) >= 3 else "MEDIUM" if len(found) >= 2 else "LOW"
    
    return (
        f"Spam Risk: {risk_level}\n"
        f"Trigger words found ({len(found)}): {', '.join(found)}\n"
        f"Recommendation: Replace or rephrase these words to avoid spam filters."
    )


@tool
def check_grammar(content: str) -> str:
    """Basic grammar and style check for email content.
    
    Args:
        content: Email content to check
    
    Returns:
        List of potential grammar/style issues.
    """
    issues = [] #mistakes ko store krne k liy list
    
    # Check for double spaces
    if "  " in content:
        issues.append("Double spaces found - clean up spacing")
    
    # Check for excessive exclamation marks
    if content.count("!") > 3:
        issues.append(f"Excessive exclamation marks ({content.count('!')} found) - tone down")
    
    # Check for ALL CAPS words (3+ chars)
    caps_words = re.findall(r'\b[A-Z]{3,}\b', content)
    if caps_words:
        issues.append(f"All-caps words found: {caps_words} - use italics/bold instead")
    
    # Check subject length (if first line)
    lines = content.strip().split('\n')
    if lines and len(lines[0]) > 60:
        issues.append(f"Subject line too long ({len(lines[0])} chars) - keep under 50 chars")
    
    # Check for placeholder issues
    if "{name}" in content:
        issues.append("Placeholder {name} found - ensure personalization is set up")
    
    # Check email length
    word_count = len(content.split())
    if word_count > 250:
        issues.append(f"Email is long ({word_count} words) - consider trimming to under 200 words")
    elif word_count < 30:
        issues.append(f"Email is very short ({word_count} words) - may lack substance")
    
    if not issues:
        return "Grammar/Style: CLEAN - No issues detected."
    
    return "Grammar/Style Issues:\n- " + "\n- ".join(issues)


# ─── Helper Functions (not tools) ───────────────────────

def save_email_to_db(brief, email_type, final_draft, scores, revision_count, status):
    """Save the final email to database."""
    db = get_db()
    db.execute(
        """INSERT INTO emails 
           (brief, email_type, final_draft, tone_score, persuasion_score, 
            cta_score, grammar_score, revision_count, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (brief, email_type, final_draft,
         scores.get("tone", 0), scores.get("persuasion", 0),
         scores.get("cta", 0), scores.get("grammar", 0),
         revision_count, status)
    )
    db.commit()


def get_email_history(limit: int = 5): #limit is optional and defaults to 5
    """Get past emails for context."""
    db = get_db()
    return db.execute(
        "SELECT * FROM emails ORDER BY created_at DESC LIMIT ?",
        (limit,) 
    ).fetchall()


# ─── All Tools List ─────────────────────────────────────
WRITER_TOOLS = [get_email_templates, check_grammar]
REVIEWER_TOOLS = [check_spam_score, check_grammar]