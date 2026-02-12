from app import app, db, User

with app.app_context():
    try:
        print("Attempting to query user...")
        user = User.query.first()
        print(f"User found: {user}")
    except Exception as e:
        print(f"Error querying user: {e}")
