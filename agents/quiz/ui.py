
# agents/quiz/ui.py
import streamlit as st
import json
import os
import tempfile
from langchain_core.messages import HumanMessage

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
            "current_answers": [],
            "quiz_active": False,
            "question_index": 0
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
                # Call extract tool directly
                from agents.quiz.tools import extract_pdf_text
                result = extract_pdf_text.invoke({"pdf_path": tmp_path})
                
                if "SUCCESS" in result:
                    # Extract doc_id from result
                    import re
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
                placeholder="e.g., photosynthesis, Python loops, World War 2",
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
2. Generate {num_questions} {question_type} questions in JSON format
3. Use save_quiz to save the quiz
4. Output the quiz questions in this format:

QUIZ READY!
Topic: {topic}
Difficulty: {difficulty}
Questions: {num_questions}

QUESTIONS (JSON):
[output the JSON array of questions]

Also display questions in readable format for the student.
"""
                    response = agent.run(
                        user_input,
                        thread_id=f"quiz-gen-{st.session_state.quiz_state['doc_id']}-{hash(topic) % 10000}"
                    )
                    
                    st.session_state.quiz_state["current_quiz"] = response
                    st.session_state.quiz_state["quiz_active"] = True
                    st.session_state.quiz_state["current_answers"] = []
                    st.session_state.quiz_state["question_index"] = 0
                    st.session_state.quiz_state["current_topic"] = topic
        
        # ─── Step 3: Display Quiz ──────────────────────
        if st.session_state.quiz_state["quiz_active"] and st.session_state.quiz_state["current_quiz"]:
            st.markdown("---")
            st.markdown("#### 📝 Step 3: Take the Quiz")
            
            # Try to extract JSON from response
            response = st.session_state.quiz_state["current_quiz"]
            
            # Show raw response in expander
            with st.expander("View Agent Response"):
                st.markdown(response)
            
            # Try to parse quiz JSON
            try:
                # Find JSON array in response
                import re
                json_match = re.search(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)
                if json_match:
                    questions = json.loads(json_match.group(0))
                    
                    st.markdown(f"**Topic:** {st.session_state.quiz_state.get('current_topic', 'N/A')}")
                    st.markdown(f"**Questions:** {len(questions)}")
                    st.markdown("---")
                    
                    # Collect answers
                    student_answers = []
                    for i, q in enumerate(questions):
                        st.markdown(f"**Q{i+1}.** {q.get('question', 'N/A')}")
                        
                        if q.get('type') == 'mcq':
                            options = q.get('options', [])
                            answer = st.radio(
                                f"Select answer for Q{i+1}",
                                options,
                                key=f"q_{i}",
                                label_visibility="collapsed"
                            )
                            # Extract just the letter (A, B, C, D)
                            student_answers.append(answer[0] if answer else "")
                        
                        elif q.get('type') == 'true_false':
                            answer = st.radio(
                                f"Select answer for Q{i+1}",
                                ["True", "False"],
                                key=f"q_{i}",
                                label_visibility="collapsed"
                            )
                            student_answers.append(answer)
                        
                        elif q.get('type') == 'short_answer':
                            answer = st.text_input(
                                f"Your answer for Q{i+1}",
                                key=f"q_{i}",
                                label_visibility="collapsed"
                            )
                            student_answers.append(answer)
                        
                        st.markdown("")
                    
                    # Submit quiz
                    if st.button("✅ Submit Quiz", type="primary"):
                        with st.spinner("Evaluating answers..."):
                            # Prepare evaluation input
                            questions_json = json.dumps(questions)
                            answers_json = json.dumps(student_answers)
                            
                            eval_input = f"""
Please evaluate this quiz attempt:

QUESTIONS JSON:
{questions_json}

STUDENT ANSWERS JSON:
{answers_json}

Process:
1. Use evaluate_answers tool with the questions and student answers
2. Use update_mastery to update mastery for topic: {st.session_state.quiz_state.get('current_topic', 'general')}
3. Show detailed results:
   - Score (X/Y = Z%)
   - Per-question breakdown (correct/wrong)
   - Explanations for wrong answers
   - Recommended next difficulty
"""
                            eval_response = agent.run(
                                eval_input,
                                thread_id=f"quiz-eval-{st.session_state.quiz_state['doc_id']}-{hash(str(student_answers)) % 10000}"
                            )
                            
                            st.markdown("---")
                            st.markdown("#### 📊 Quiz Results")
                            st.markdown(eval_response)
                            
                            # Reset quiz state
                            st.session_state.quiz_state["quiz_active"] = False
                            st.session_state.quiz_state["current_quiz"] = None
                
                else:
                    st.info("Quiz generated. Check the agent response above for details.")
                    
            except json.JSONDecodeError as e:
                st.warning(f"Could not parse quiz JSON: {e}")
                st.info("Check the agent response above for the quiz.")
            except Exception as e:
                st.error(f"Error: {e}")
    
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