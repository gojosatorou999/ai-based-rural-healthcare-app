
import os
import app
from app import db, app as flask_app

def fix_database():
    db_path = os.path.join(os.getcwd(), 'instance', 'database.db')
    print(f"Checking database at: {db_path}")
    
    if os.path.exists(db_path):
        print("Removing existing database...")
        try:
            os.remove(db_path)
            print("Database removed successfully.")
        except PermissionError:
            print("Error: Could not remove database file. It might be in use.")
            print("Please CLOSE the running application window (cmd/terminal) and try again.")
            return
        except Exception as e:
            print(f"Error removing database: {e}")
            return
    else:
        print("No existing database found.")

    print("Creating new database schema...")
    with flask_app.app_context():
        try:
            db.create_all()
            print("Database and tables created successfully!")
            print("You can now restart the application.")
        except Exception as e:
            print(f"Error creating database: {e}")

if __name__ == "__main__":
    fix_database()
