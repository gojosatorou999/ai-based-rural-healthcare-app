
from app import app, db, User, bcrypt
import sys

with app.app_context():
    email = 'doc@gmail.com'
    if User.query.filter_by(email=email).first():
        print(f"User {email} already exists.")
        sys.exit(0)
    
    hashed_pw = bcrypt.generate_password_hash('doc123').decode('utf-8')
    admin_user = User(
        username='Medical Admin',
        email=email,
        password=hashed_pw,
        role='doctor',
        age=45,
        gender='Male'
    )
    db.session.add(admin_user)
    db.session.commit()
    print(f"Successfully created admin user: {email}")
