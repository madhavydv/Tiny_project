import sqlite3
import bcrypt

def reset_passwords():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Get all users
    c.execute('SELECT email FROM users')
    users = c.fetchall()
    
    for user in users:
        email = user[0]
        # Set a default password (you can change this)
        default_password = "password123"
        hashed_pw = bcrypt.hashpw(default_password.encode(), bcrypt.gensalt())
        hashed_pw_str = hashed_pw.decode('utf-8')
        
        # Update the password
        c.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_pw_str, email))
        print(f"Reset password for user: {email}")
    
    conn.commit()
    conn.close()
    print("All passwords have been reset")

if __name__ == "__main__":
    reset_passwords()