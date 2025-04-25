import sqlite3
from datetime import datetime

def init_db():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create quiz_results table
    c.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(email, password):
    """Add a new user to the database"""
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("User already exists")
    finally:
        conn.close()

def login_user(email, password):
    """Verify user credentials"""
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    
    c.execute('SELECT password FROM users WHERE email = ?', (email,))
    result = c.fetchone()
    
    conn.close()
    
    if result and result[0] == password:
        return True
    return False

def store_quiz_result(user_email, subject, topic, difficulty, score, total_questions):
    """Store a quiz result in the database"""
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO quiz_results 
            (user_email, subject, topic, difficulty, score, total_questions, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_email, subject, topic, difficulty, score, total_questions, datetime.now()))
        conn.commit()
    except Exception as e:
        print(f"Error storing quiz result: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_user_scores(user_email):
    """Get all quiz scores for a user"""
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT subject, topic, difficulty, score, total_questions, timestamp
        FROM quiz_results
        WHERE user_email = ?
        ORDER BY timestamp DESC
    ''', (user_email,))
    
    results = c.fetchall()
    conn.close()
    
    return results

def get_user_stats(user_email):
    """Get user statistics"""
    conn = sqlite3.connect('quiz_app.db')
    c = conn.cursor()
    
    # Get total quizzes taken
    c.execute('SELECT COUNT(*) FROM quiz_results WHERE user_email = ?', (user_email,))
    total_quizzes = c.fetchone()[0]
    
    # Get average score
    c.execute('''
        SELECT AVG(CAST(score AS FLOAT) / total_questions * 100)
        FROM quiz_results
        WHERE user_email = ?
    ''', (user_email,))
    avg_score = c.fetchone()[0] or 0
    
    # Get highest score
    c.execute('''
        SELECT MAX(CAST(score AS FLOAT) / total_questions * 100)
        FROM quiz_results
        WHERE user_email = ?
    ''', (user_email,))
    highest_score = c.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'total_quizzes': total_quizzes,
        'avg_score': round(avg_score, 1),
        'highest_score': round(highest_score, 1)
    }