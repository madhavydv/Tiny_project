import sqlite3

DB_NAME = "users.db"

def signup(email, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login(email, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    result = c.fetchone()
    conn.close()
    return result is not None

def update_progress(email, score):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT progress FROM users WHERE email=?", (email,))
    old = c.fetchone()[0]
    new_progress = (old + score) / 2
    c.execute("UPDATE users SET progress=? WHERE email=?", (new_progress, email))
    conn.commit()
    conn.close()

def get_user_progress(email):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT progress FROM users WHERE email=?", (email,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0