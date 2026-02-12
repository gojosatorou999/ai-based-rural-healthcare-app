from app import app, db, User, bcrypt

with app.app_context():
    # Check if user already exists
    email = 'chw@gmail.com'
    existing_user = User.query.filter_by(email=email).first()
    
    if existing_user:
        print(f"User {email} already exists. Updating password and role.")
        existing_user.password = bcrypt.generate_password_hash('chw123').decode('utf-8')
        existing_user.role = 'chw'
        existing_user.username = 'Community Health Worker'
    else:
        print(f"Creating new CHW user: {email}")
        new_user = User(
            username='Community Health Worker',
            email=email,
            password=bcrypt.generate_password_hash('chw123').decode('utf-8'),
            role='chw',
            preferred_language='english'
        )
        db.session.add(new_user)
    
    db.session.commit()
    print("CHW user setup complete!")
