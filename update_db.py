from app import app, db

if __name__ == "__main__":
    print("Updating database schema...")
    with app.app_context():
        try:
            db.create_all()
            print("Database updated successfully! New tables created.")
        except Exception as e:
            print(f"Error updating database: {e}")
