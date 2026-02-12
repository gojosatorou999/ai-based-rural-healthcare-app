from app import app, db, User
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('user')]
    print(f"User columns: {columns}")
    
    if 'whatsapp_number' not in columns:
        print("MISSING 'whatsapp_number'. Adding it now...")
        with db.engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("ALTER TABLE user ADD COLUMN whatsapp_number VARCHAR(20)"))
            conn.execute(text("ALTER TABLE user ADD COLUMN family_whatsapp VARCHAR(20)"))
            conn.commit()
        print("Columns added successfully!")
    else:
        print("'whatsapp_number' already exists.")
