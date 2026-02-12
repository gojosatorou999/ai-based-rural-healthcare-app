from app import app, db, User
with app.app_context():
    users = User.query.all()
    for u in users:
        print(f'User: {u.username}, Role: {u.role}, WhatsApp: {u.whatsapp_number}, Family: {u.family_whatsapp}')
