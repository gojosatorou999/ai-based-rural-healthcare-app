from app import app, db, User, bcrypt

def create_doctor():
    with app.app_context():
        # Check if doctor exists
        doctor = User.query.filter_by(username='doc').first()
        
        if doctor:
            print("Doctor account 'doc' already exists.")
            # Optional: Reset password if it exists to ensure 'doc123' works
            doctor.password = bcrypt.generate_password_hash('doc123').decode('utf-8')
            doctor.role = 'doctor'
            db.session.commit()
            print("Password reset to 'doc123' and role confirmed as 'doctor'.")
        else:
            hashed_password = bcrypt.generate_password_hash('doc123').decode('utf-8')
            new_doctor = User(
                username='doc',
                email='doc@pristin.com',
                password=hashed_password,
                role='doctor',
                age=35,
                gender='Other',
                preferred_language='english'
            )
            db.session.add(new_doctor)
            db.session.commit()
            print("Doctor account created successfully!")
            print("Username: doc")
            print("Password: doc123")

if __name__ == "__main__":
    create_doctor()
