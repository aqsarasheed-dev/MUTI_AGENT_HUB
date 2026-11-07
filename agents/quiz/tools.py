# agents/quiz/tools.py
import sqlite3
import json
import os
import tempfile
from langchain_core.tools import tool
from functools import lru_cache

# ─── Database Setup ─────────────────────────────────────
DB_PATH = "database/quiz.db"

@lru_cache(maxsize=1)
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_quiz_db():
    """Create tables for quiz system. Run once."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            content TEXT,
            word_count INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,
            topic TEXT,
            difficulty TEXT,
            questions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doc_id) REFERENCES documents(id)
        );
        
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            student_answers TEXT,
            score REAL,
            total_questions INTEGER,
            correct_answers INTEGER,
            feedback TEXT,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
        );
        
        CREATE TABLE IF NOT EXISTS mastery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT UNIQUE,
            mastery_score REAL DEFAULT 0,
            attempts_count INTEGER DEFAULT 0,
            last_attempted TIMESTAMP
        );
    """)
    db.commit()


# ─── PDF Extraction ────────────────────────────────────

@tool
def extract_pdf_text(pdf_path: str) -> str:
    """Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Extracted text content with word count, or error message.
    """
    try:
        # Try PyMuPDF first (best for text PDFs)
        try:
            fitz = __import__("fitz")  # PyMuPDF
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            if len(text.strip()) < 50:
                return "PDF contains too little text. Might be scanned/image PDF. OCR not available."
            
            # Save to DB
            db = get_db()
            cursor = db.execute(
                "INSERT INTO documents (filename, content, word_count) VALUES (?, ?, ?)",
                (os.path.basename(pdf_path), text, len(text.split()))
            )
            db.commit()
            
            return f"SUCCESS: Extracted {len(text.split())} words from {os.path.basename(pdf_path)}. Doc ID: {cursor.lastrowid}\n\nPreview (first 500 chars):\n{text[:500]}..."
        
        except ImportError:
            # Fallback to pypdf
            try:
                PdfReader = __import__("pypdf", fromlist=["PdfReader"]).PdfReader
                reader = PdfReader(pdf_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                if len(text.strip()) < 50:
                    return "PDF contains too little text. Might be scanned/image PDF."
                
                db = get_db()
                cursor = db.execute(
                    "INSERT INTO documents (filename, content, word_count) VALUES (?, ?, ?)",
                    (os.path.basename(pdf_path), text, len(text.split()))
                )
                db.commit()
                
                return f"SUCCESS: Extracted {len(text.split())} words from {os.path.basename(pdf_path)}. Doc ID: {cursor.lastrowid}\n\nPreview (first 500 chars):\n{text[:500]}..."
            
            except ImportError:
                return "ERROR: No PDF library installed. Run: pip install pymupdf"
    
    except Exception as e:
        return f"ERROR extracting PDF: {str(e)}"


@tool
def retrieve_relevant_content(doc_id: int, topic: str, max_chars: int = 5000) -> str:
    """Retrieve relevant content from uploaded document for quiz generation.
    This is the RAG component - finds text relevant to the quiz topic.
    
    Args:
        doc_id: Document ID from extract_pdf_text
        topic: Topic to generate quiz about (e.g., "photosynthesis", "Python loops")
        max_chars: Maximum content to retrieve (default 5000)
    
    Returns:
        Relevant text chunks from the document.
    """
    db = get_db()
    row = db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    
    if not row:
        return f"Document with ID {doc_id} not found."
    
    content = row["content"]
    topic_lower = topic.lower()
    
    # Simple keyword-based retrieval (in production, use vector embeddings)
    sentences = content.replace('\n', ' ').split('. ')
    
    relevant = []
    other = []
    
    for sent in sentences:
        if topic_lower in sent.lower():
            relevant.append(sent)
        else:
            other.append(sent)
    
    # Take relevant sentences first, then fill with other content
    result_text = '. '.join(relevant[:20]) if relevant else ""
    
    if len(result_text) < max_chars:
        remaining = max_chars - len(result_text)
        for sent in other:
            if len(result_text) >= max_chars:
                break
            result_text += '. ' + sent
    
    if not result_text:
        result_text = content[:max_chars]
    
    return f"Retrieved content for topic '{topic}' (Doc ID: {doc_id}):\n\n{result_text[:max_chars]}"


@tool
def generate_quiz_questions(
    content: str, 
    topic: str, 
    difficulty: str = "medium",
    num_questions: int = 5,
    question_types: str = "mcq"
) -> str:
    """Generate quiz questions from content (called by LLM - returns instructions).
    
    Args:
        content: Source content to base questions on
        topic: Quiz topic
        difficulty: easy, medium, or hard
        num_questions: Number of questions (default 5)
        question_types: mcq, true_false, short_answer, or mixed
    
    Returns:
        Instructions for LLM to generate questions.
    """
    # This tool provides context to the LLM - the actual generation is done by LLM
    return (
        f"QUIZ GENERATION TASK:\n"
        f"Topic: {topic}\n"
        f"Difficulty: {difficulty}\n"
        f"Number of questions: {num_questions}\n"
        f"Question type: {question_types}\n\n"
        f"SOURCE CONTENT:\n{content[:3000]}\n\n"
        f"Generate {num_questions} {difficulty} {question_types} questions. "
        f"Questions MUST be answerable from the source content above. "
        f"Do NOT make up questions about topics not in the content."
    )


@tool
def evaluate_answers(
    questions_json: str,
    student_answers_json: str
) -> str:
    """Evaluate student answers against correct answers.
    
    Args:
        questions_json: JSON string of questions with correct answers
        student_answers_json: JSON string of student's answers
    
    Returns:
        Score, correct count, and per-question evaluation.
    """
    try:
        questions = json.loads(questions_json)
        student_answers = json.loads(student_answers_json)
    except json.JSONDecodeError as e:
        return f"ERROR parsing JSON: {e}"
    
    if len(questions) != len(student_answers):
        return f"Mismatch: {len(questions)} questions but {len(student_answers)} answers"
    
    results = []
    correct_count = 0
    
    for i, (q, a) in enumerate(zip(questions, student_answers)):
        is_correct = str(a).strip().lower() == str(q.get("answer", "")).strip().lower()
        if is_correct:
            correct_count += 1
        
        results.append({
            "question_num": i + 1,
            "question": q.get("question", ""),
            "student_answer": a,
            "correct_answer": q.get("answer", ""),
            "is_correct": is_correct,
            "explanation": q.get("explanation", "No explanation provided")
        })
    
    score = (correct_count / len(questions)) * 100
    
    return json.dumps({
        "score": score,
        "correct_count": correct_count,
        "total_questions": len(questions),
        "results": results
    }, indent=2)


@tool
def update_mastery(topic: str, score: float) -> str:
    """Update mastery score for a topic after quiz attempt.
    
    Args:
        topic: Quiz topic
        score: Score percentage (0-100)
    
    Returns:
        Updated mastery info + difficulty recommendation.
    """
    db = get_db()
    
    # Get current mastery
    row = db.execute("SELECT * FROM mastery WHERE topic = ?", (topic,)).fetchone()
    
    if row:
        # Update with weighted average (70% old, 30% new)
        old_score = row["mastery_score"]
        new_score = (old_score * 0.7) + (score * 0.3)
        new_count = row["attempts_count"] + 1
        
        db.execute(
            "UPDATE mastery SET mastery_score = ?, attempts_count = ?, last_attempted = CURRENT_TIMESTAMP WHERE topic = ?",
            (new_score, new_count, topic)
        )
    else:
        new_score = score
        new_count = 1
        db.execute(
            "INSERT INTO mastery (topic, mastery_score, attempts_count, last_attempted) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (topic, score, new_count)
        )
    
    db.commit()
    
    # Recommend next difficulty
    if new_score >= 85:
        next_difficulty = "hard"
        level = "Advanced"
    elif new_score >= 60:
        next_difficulty = "medium"
        level = "Intermediate"
    else:
        next_difficulty = "easy"
        level = "Beginner"
    
    return (
        f"Mastery updated for '{topic}':\n"
        f"  New Score: {new_score:.1f}%\n"
        f"  Attempts: {new_count}\n"
        f"  Level: {level}\n"
        f"  Recommended next difficulty: {next_difficulty}"
    )


@tool
def get_mastery_history() -> str:
    """Get mastery scores for all topics attempted.
    
    Returns:
        List of topics with mastery scores and attempt counts.
    """
    db = get_db()
    rows = db.execute(
        "SELECT * FROM mastery ORDER BY last_attempted DESC"
    ).fetchall()
    
    if not rows:
        return "No mastery data yet. Take some quizzes!"
    
    results = ["MASTERY DASHBOARD:\n"]
    for r in rows:
        level = "Advanced" if r["mastery_score"] >= 85 else "Intermediate" if r["mastery_score"] >= 60 else "Beginner"
        bar = "█" * int(r["mastery_score"] / 10) + "░" * (10 - int(r["mastery_score"] / 10))
        
        results.append(
            f"{r['topic']:<25} {bar} {r['mastery_score']:.1f}% ({level}) - {r['attempts_count']} attempts"
        )
    
    return "\n".join(results)


# ─── Direct DB Helper (NOT a tool, called by UI) ────────
def save_quiz_directly(doc_id: int, topic: str, difficulty: str, num_questions: int) -> int:
    """Save quiz metadata directly to DB (not as a tool, called by UI).
    This bypasses the LLM to avoid JSON parsing errors with large question strings.
    """
    db = get_db()
    cursor = db.execute(
        "INSERT INTO quizzes (doc_id, topic, difficulty, questions) VALUES (?, ?, ?, ?)",
        (doc_id, topic, difficulty, f"Generated {num_questions} questions")
    )
    db.commit()
    return cursor.lastrowid


# ─── All Tools List (save_quiz REMOVED to prevent JSON errors) ───
ALL_TOOLS = [
    extract_pdf_text,
    retrieve_relevant_content,
    generate_quiz_questions,
    evaluate_answers,
    update_mastery,
    get_mastery_history,
]