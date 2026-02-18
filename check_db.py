import sqlite3
import os

db_path = 'c:/Users/risha/Documents/antigrav/instance/database.db'
if not os.path.exists(db_path):
    db_path = 'c:/Users/risha/Documents/antigrav/database.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, email, role FROM user")
        users = cursor.fetchall()
        print("Users in database:")
        for user in users:
            print(user)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database not found at {db_path}")
