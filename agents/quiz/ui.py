# agents/quiz/ui.py
import streamlit as st
import json
import os
import re
import tempfile


def parse_quiz_response(response: str) -> list:
    """Parse LLM quiz response into structured data.
    Handles both single-line and multi-line formats.
    """
    import re
    quiz_data = []
    
    # Split by Q1., Q2., etc.
    pattern = r'Q(\d+)\.\s*(.+?)(?=(?:Q\d+\.|$))'
    matches = re.findall(pattern, response, re.DOTALL)
    
    for q_num, q_content in matches:
        q_data = {
            "question_num": int(q_num),
            "question": "",
            "options": [],
            "answer": "",
            "explanation": ""
        }
        
        # Normalize whitespace (convert newlines to spaces, collapse multiple spaces)
        content = ' '.join(q_content.split())
        
        # Extract Answer (letter A-D)
        ans_match = re.search(r'Answer:\s*([A-D])', content, re.IGNORECASE)
        if ans_match:
            q_data["answer"] = ans_match.group(1).upper()
        else:
            # Try True/False or text answer
            ans_match = re.search(r'Answer:\s*(.+?)(?=\s*Explanation:|$)', content, re.IGNORECASE)
            if ans_match:
                q_data["answer"] = ans_match.group(1).strip()
        
        # Extract Explanation (everything after "Explanation:")
        exp_match = re.search(r'Explanation:\s*(.+)', content, re.IGNORECASE)
        if exp_match:
            q_data["explanation"] = exp_match.group(1).strip()
        
        # Remove Answer and Explanation sections for option parsing
        content_clean = re.sub(r'\s*Answer:.*$', '', content, flags=re.IGNORECASE)
        
        # Now parse: <question> A) <opt1> B) <opt2> C) <opt3> D) <opt4>
        # Split by option markers (space + letter + closing paren + space)
        parts = re.split(r'\s+([A-D])\)\s+', content_clean)
        
        if len(parts) > 1:
            # First part is the question
            q_data["question"] = parts[0].strip()
            
            # Remaining parts alternate: letter, text, letter, text, ...
            for i in range(1, len(parts), 2):
                letter = parts[i]
                if i + 1 < len(parts):
                    text = parts[i + 1].strip()
                else:
                    text = ""
                q_data["options"].append(f"{letter}) {text}")
        else:
            # No options found - might be short answer
            q_data["question"] = content_clean.strip()
        
        if q_data["question"]:
            quiz_data.append(q_data)
    
    return quiz_data


def render_quiz_ui(agent):
    """Streamlit UI for QuizMaster Pro agent."""
    
    st.markdown("### 📝 QuizMaster Pro — PDF-Based Adaptive Quiz")
    st.markdown("Upload a PDF, generate quizzes, attempt, get evaluated, and track mastery.")
    
    # ─── Initialize Session State ──────────────────────
    if "quiz_state" not in st.session_state:
        st.session_state.quiz_state = {
            "pdf_uploaded": False,
            "doc_id": None,
            "current_quiz": None,
            "current_topic": "",
            "quiz_active": False,
        }
    
    # ─── Step 1: PDF Upload ────────────────────────────
    st.markdown("#### 📄 Step 1: Upload PDF")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload notes, textbook chapter, or any study material"
    )
    
    if uploaded_file is not None:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        if st.button("Process PDF", type="primary"):
            with st.spinner("Extracting text from PDF..."):
                from agents.quiz.tools import extract_pdf_text
                result = extract_pdf_text.invoke({"pdf_path": tmp_path})
                
                if "SUCCESS" in result:
                    match = re.search(r'Doc ID: (\d+)', result)
                    if match:
                        st.session_state.quiz_state["doc_id"] = int(match.group(1))
                        st.session_state.quiz_state["pdf_uploaded"] = True
                        st.success(f"✅ PDF processed! {result.split('Preview')[0].strip()}")
                    else:
                        st.error("Could not extract document ID")
                else:
                    st.error(result)
        
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass
    
    # ─── Step 2: Quiz Configuration ───────────────────
    if st.session_state.quiz_state["pdf_uploaded"]:
        st.markdown("---")
        st.markdown("#### ⚙️ Step 2: Configure Quiz")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            topic = st.text_input(
                "📚 Topic",
                placeholder="e.g., photosynthesis, Python loops, CPU",
                help="What topic should the quiz cover?"
            )
        
        with col2:
            difficulty = st.selectbox(
                "📊 Difficulty",
                ["easy", "medium", "hard"],
                help="Easy: basic recall | Medium: understanding | Hard: application"
            )
        
        with col3:
            num_questions = st.slider(
                "🔢 Number of Questions",
                min_value=3,
                max_value=15,
                value=5
            )
        
        question_type = st.selectbox(
            "📝 Question Type",
            ["mcq", "true_false", "short_answer", "mixed"],
            help="MCQ: multiple choice | T/F: true/false | Short: written answer | Mixed: combination"
        )
        
        if st.button("🎯 Generate Quiz", type="primary"):
            if not topic.strip():
                st.warning("Please enter a topic first.")
            else:
                with st.spinner(f"Generating {difficulty} quiz on '{topic}'..."):
                    user_input = f"""
Please generate a quiz with these specifications:
- Doc ID: {st.session_state.quiz_state['doc_id']}
- Topic: {topic}
- Difficulty: {difficulty}
- Number of questions: {num_questions}
- Question type: {question_type}

Process:
1. Use retrieve_relevant_content to get content for the topic from the PDF
2. Generate {num_questions} {question_type} questions
3. Output the quiz in this EXACT format:

QUIZ READY!
Topic: {topic}
Difficulty: {difficulty}
Questions: {num_questions}

Q1. [Question text]
A) [option 1]
B) [option 2]
C) [option 3]
D) [option 4]
Answer: [correct letter]
Explanation: [why this is correct]

Q2. [Question text]
A) [option 1]
B) [option 2]
C) [option 3]
D) [option 4]
Answer: [correct letter]
Explanation: [why this is correct]

(continue for all {num_questions} questions)

Do NOT call any save tool. Just output the questions in the format above.
"""
                    response = agent.run(
                        user_input,
                        thread_id=f"quiz-gen-{st.session_state.quiz_state['doc_id']}-{hash(topic) % 10000}"
                    )
                    
                    # Save quiz to DB directly
                    try:
                        from agents.quiz.tools import save_quiz_directly
                        quiz_id = save_quiz_directly(
                            doc_id=st.session_state.quiz_state['doc_id'],
                            topic=topic,
                            difficulty=difficulty,
                            num_questions=num_questions
                        )
                        st.success(f"✅ Quiz saved to database (ID: {quiz_id})")
                    except Exception as e:
                        st.warning(f"Could not save to DB: {e}")
                    
                    st.session_state.quiz_state["current_quiz"] = response
                    st.session_state.quiz_state["current_topic"] = topic
                    st.session_state.quiz_state["quiz_active"] = True
    
    # ─── Step 3: Display Quiz ──────────────────────
    if st.session_state.quiz_state["quiz_active"] and st.session_state.quiz_state["current_quiz"]:
        st.markdown("---")
        st.markdown("#### 📝 Step 3: Take the Quiz")
        
        response = st.session_state.quiz_state["current_quiz"]
        
        # Parse the structured quiz format
        quiz_data = parse_quiz_response(response)
        
        if quiz_data and len(quiz_data) > 0:
            st.markdown(f"**Topic:** {st.session_state.quiz_state.get('current_topic', 'N/A')}")
            st.markdown(f"**Questions:** {len(quiz_data)}")
            st.markdown("---")
            
            # Display questions WITHOUT answers
            student_answers = {}
            for i, q in enumerate(quiz_data):
                st.markdown(f"**Q{i+1}.** {q['question']}")
                
                if q.get('options') and len(q['options']) > 0:
                    # MCQ or True/False
                    answer = st.radio(
                        f"Select your answer for Q{i+1}",
                        q['options'],
                        key=f"q_{i}",
                        label_visibility="collapsed"
                    )
                    # Extract just the letter (A, B, C, D)
                    student_answers[i] = answer[0] if answer else ""
                else:
                    # Short answer
                    answer = st.text_input(
                        f"Your answer for Q{i+1}",
                        key=f"q_{i}",
                        label_visibility="collapsed"
                    )
                    student_answers[i] = answer
                
                st.markdown("")
            
            # Submit button
            if st.button("✅ Submit Quiz", type="primary"):
                with st.spinner("Evaluating your answers..."):
                    # Evaluate locally (no LLM needed)
                    correct_count = 0
                    results = []
                    
                    for i, q in enumerate(quiz_data):
                        user_ans = str(student_answers[i]).strip().lower()
                        correct_ans = str(q.get('answer', '')).strip().lower()
                        
                        # Direct match
                        is_correct = user_ans == correct_ans

                        # If no match, try first character match (for A/B/C/D)
                        if not is_correct and len(user_ans) > 0 and len(correct_ans) > 0:
                            is_correct = user_ans[0] == correct_ans[0]

                        # Also try if correct answer text is in the student's selected option
                        if not is_correct and len(user_ans) > 0:
                            is_correct = correct_ans in user_ans
                        if is_correct:
                            correct_count += 1
                        
                        results.append({
                            "question_num": i + 1,
                            "question": q['question'],
                            "student_answer": student_answers[i],
                            "correct_answer": q.get('answer', ''),
                            "is_correct": is_correct,
                            "explanation": q.get('explanation', 'No explanation')
                        })
                    
                    score = (correct_count / len(quiz_data)) * 100 if quiz_data else 0
                    
                    # Display results
                    st.markdown("---")
                    st.markdown("#### 📊 Quiz Results")
                    
                    # Score banner
                    if score >= 80:
                        st.success(f"🎉 Excellent! You scored {correct_count}/{len(quiz_data)} ({score:.0f}%)")
                    elif score >= 60:
                        st.warning(f"👍 Good effort! You scored {correct_count}/{len(quiz_data)} ({score:.0f}%)")
                    else:
                        st.error(f"📚 Keep practicing! You scored {correct_count}/{len(quiz_data)} ({score:.0f}%)")
                    
                    # Per-question breakdown
                    st.markdown("---")
                    st.markdown("#### 📋 Detailed Review")
                    
                    for r in results:
                        icon = "✅" if r['is_correct'] else "❌"
                        with st.expander(f"{icon} Q{r['question_num']}: {r['question'][:60]}..."):
                            st.markdown(f"**Question:** {r['question']}")
                            st.markdown(f"**Your Answer:** {r['student_answer']}")
                            st.markdown(f"**Correct Answer:** {r['correct_answer']}")
                            st.markdown(f"**Explanation:** {r['explanation']}")
                    
                    # Update mastery using tool
                    try:
                        from agents.quiz.tools import update_mastery
                        topic_name = st.session_state.quiz_state.get('current_topic', 'general')
                        mastery_msg = update_mastery.invoke({
                            "topic": topic_name,
                            "score": float(score)
                        })
                        st.markdown("---")
                        st.markdown("#### 📈 Mastery Updated")
                        st.code(mastery_msg)
                    except Exception as e:
                        st.warning(f"Could not update mastery: {e}")
                    
                    # Reset quiz state
                    st.session_state.quiz_state["quiz_active"] = False
                    st.session_state.quiz_state["current_quiz"] = None
        
        else:
            # Fallback: Show raw response if parsing fails
            st.info("Quiz generated. Check the response below:")
            with st.expander("View Quiz (Raw Format)"):
                st.markdown(response)
    
    # ─── Mastery Dashboard ────────────────────────────
    st.markdown("---")
    st.markdown("#### 📊 Mastery Dashboard")
    
    if st.button("View My Mastery"):
        with st.spinner("Loading mastery data..."):
            from agents.quiz.tools import get_mastery_history
            mastery = get_mastery_history.invoke({})
            st.code(mastery)
    
    # ─── Tips ─────────────────────────────────────────
    with st.expander("💡 Tips for Best Results"):
        st.markdown("""
        **PDF Requirements:**
        - Text-based PDF (not scanned images)
        - At least 1 page of content
        - Clear topic coverage
        
        **Topic Tips:**
        - Be specific: "photosynthesis" not "biology"
        - Match topic to PDF content
        - One topic per quiz for best results
        
        **Difficulty Guide:**
        - **Easy**: Basic recall, definitions, facts
        - **Medium**: Understanding, explanations, comparisons
        - **Hard**: Application, analysis, synthesis
        
        **Question Types:**
        - **MCQ**: Best for quick assessment
        - **True/False**: Best for facts and concepts
        - **Short Answer**: Best for deep understanding
        - **Mixed**: Variety for comprehensive assessment
        """)