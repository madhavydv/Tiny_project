import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import streamlit as st
from database import init_db, add_user, login_user, store_quiz_result, get_user_scores, get_user_stats
from quiz_generator import generate_quiz_questions, evaluate_quiz
import math

# Initialize the database
init_db()

def display_quiz(questions):
    """Display quiz questions and collect answers"""
    if not questions:
        st.error("No questions could be generated. Please try a different topic.")
        return None
    
    st.write("### Quiz Questions")
    st.write("Select your answer for each question:")
    
    answers = {}
    for i, question in enumerate(questions, 1):
        st.write(f"\n**Question {i}:** {question['question']}")
        
        # Create columns for options
        col1, col2 = st.columns(2)
        with col1:
            st.write("**A.** " + question['options']['A'][:150] + "..." if len(question['options']['A']) > 150 else question['options']['A'])
            st.write("**C.** " + question['options']['C'][:150] + "..." if len(question['options']['C']) > 150 else question['options']['C'])
        with col2:
            st.write("**B.** " + question['options']['B'][:150] + "..." if len(question['options']['B']) > 150 else question['options']['B'])
            st.write("**D.** " + question['options']['D'][:150] + "..." if len(question['options']['D']) > 150 else question['options']['D'])
        
        # Add some space between options and radio buttons
        st.write("")
        
        # Create radio buttons for answers
        answer = st.radio(
            f"Your answer for Question {i}:",
            ["A", "B", "C", "D"],
            key=f"q_{i}",
            horizontal=True
        )
        answers[i] = answer
        
        # If showing results, display feedback
        if st.session_state.get('show_results', False):
            correct_answer = question['answer']
            if answer == correct_answer:
                st.success(f"✅ Correct! {question.get('explanation', '')}")
            else:
                st.error(f"❌ Incorrect. The correct answer is {correct_answer}. {question.get('explanation', '')}")
        
        # Add a divider between questions
        st.divider()
    
    return answers

def show_performance_chart(username):
    """Show the user's performance chart"""
    # Get user's quiz history
    scores = get_user_scores(username)
    if not scores:
        st.info("Take your first quiz to see your performance!")
        return
    
    # Convert scores to a pandas DataFrame
    import pandas as pd
    df = pd.DataFrame(scores, columns=['subject', 'topic', 'difficulty', 'score', 'total', 'timestamp'])
    df['percentage'] = (df['score'] / df['total']) * 100
    
    # Create performance chart
    st.write("#### Recent Quiz Scores")
    
    # Bar chart for recent scores
    chart_data = df.tail(5)  # Last 5 quizzes
    st.bar_chart(chart_data.set_index('topic')['percentage'])
    
    # Show statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_score = df['percentage'].mean()
        st.metric("Average Score", f"{avg_score:.1f}%")
    
    with col2:
        best_score = df['percentage'].max()
        st.metric("Best Score", f"{best_score:.1f}%")
    
    with col3:
        total_quizzes = len(df)
        st.metric("Total Quizzes", total_quizzes)
    
    # Show detailed history in an expander
    with st.expander("View Detailed History"):
        st.dataframe(
            df[['topic', 'subject', 'difficulty', 'score', 'total', 'percentage']].style.format({
                'percentage': '{:.1f}%'
            })
        )

def show_auth_form():
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            if login_user(email, password):
                st.session_state.user = email
                st.success("Logged in successfully")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_email = st.text_input("New Email", key="signup_email")
        new_password = st.text_input("New Password", type="password", key="signup_password")
        if st.button("Sign Up"):
            try:
                add_user(new_email, new_password)
                st.success("Signed up successfully! Please login.")
            except Exception as e:
                st.error(f"Error during signup: {str(e)}")

def main():
    st.set_page_config(page_title="AI Quiz Generator", page_icon="✍️", layout="wide")
    
    # Add custom CSS for better styling
    st.markdown("""
        <style>
        .stRadio > div {
            display: flex;
            justify-content: center;
            gap: 2rem;
        }
        .stRadio label {
            font-weight: bold;
            padding: 0.5rem 2rem;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        .stRadio label:hover {
            background-color: #f0f0f0;
        }
        .stProgress > div > div > div {
            background-color: #00cc00;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("✍️ AI Quiz Generator")
    
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Show login/signup form if user is not logged in
    if not st.session_state.user:
        show_auth_form()
        return
    
    # Show welcome message and logout button
    col1, col2 = st.columns([3,1])
    with col1:
        st.write(f"Welcome, {st.session_state.user}! 👋")
    with col2:
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()
    
    # Show performance chart
    show_performance_chart(st.session_state.user)
    
    st.write("---")
    
    # Quiz generation form
    with st.form("quiz_form"):
        st.write("### Generate a New Quiz")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            subject = st.text_input("Subject (e.g., Computer Science, History)", 
                                  placeholder="Enter the subject")
        
        with col2:
            topic = st.text_input("Topic (e.g., Python, World War II)", 
                                placeholder="Enter the topic")
        
        with col3:
            difficulty = st.selectbox("Difficulty Level", 
                                    ["beginner", "intermediate", "advanced"])
        
        num_questions = st.slider("Number of Questions", 
                                min_value=5, max_value=10, value=5,
                                help="Minimum 5 questions required for a meaningful quiz")
        
        generate_button = st.form_submit_button("Generate Quiz", type="primary")
    
    if generate_button:
        if not subject or not topic:
            st.error("Please enter both subject and topic")
        else:
            with st.spinner("Generating your quiz... This may take a moment while we gather information."):
                try:
                    questions = generate_quiz_questions(subject, topic, difficulty, num_questions)
                    
                    if questions and len(questions) >= 5:
                        st.session_state.current_quiz = {
                            'subject': subject,
                            'topic': topic,
                            'difficulty': difficulty,
                            'questions': questions
                        }
                        st.session_state.show_results = False
                        st.success(f"Generated {len(questions)} questions! Start your quiz below.")
                    else:
                        st.error("Could not generate enough questions. Please try a different topic or subject.")
                except Exception as e:
                    st.error(f"Error generating quiz: {str(e)}")
    
    # Display current quiz if it exists
    if hasattr(st.session_state, 'current_quiz') and not st.session_state.get('show_results', False):
        quiz = st.session_state.current_quiz
        
        st.write(f"### {quiz['topic']} Quiz")
        st.write(f"Subject: {quiz['subject']} | Difficulty: {quiz['difficulty'].title()}")
        
        answers = display_quiz(quiz['questions'])
        
        if answers and len(answers) >= 5:
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                if st.button("Submit Quiz", type="primary"):
                    try:
                        score = evaluate_quiz(quiz['questions'], answers)
                        total = len(quiz['questions'])
                        percentage = (score / total) * 100
                        
                        # Store the quiz result
                        store_quiz_result(
                            st.session_state.user,
                            quiz['subject'],
                            quiz['topic'],
                            quiz['difficulty'],
                            score,
                            total
                        )
                        
                        st.session_state.last_score = {
                            'score': score,
                            'total': total,
                            'percentage': percentage
                        }
                        st.session_state.show_results = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error evaluating quiz: {str(e)}")
    
    # Show results if quiz was submitted
    elif hasattr(st.session_state, 'current_quiz') and st.session_state.get('show_results', False):
        score_data = st.session_state.last_score
        st.write("### Quiz Results")
        
        # Create a progress bar for the score
        progress = score_data['percentage'] / 100
        st.progress(progress)
        
        # Show the score with appropriate emoji
        if score_data['percentage'] >= 80:
            emoji = "🌟"
        elif score_data['percentage'] >= 60:
            emoji = "👍"
        else:
            emoji = "💪"
            
        st.write(f"### {emoji} You scored {score_data['score']}/{score_data['total']} ({score_data['percentage']:.1f}%)")
        
        # Add buttons for next actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Try Again", type="secondary"):
                del st.session_state.current_quiz
                del st.session_state.show_results
                st.rerun()
        with col2:
            if st.button("New Topic", type="primary"):
                del st.session_state.current_quiz
                del st.session_state.show_results
                st.rerun()

if __name__ == "__main__":
    main()