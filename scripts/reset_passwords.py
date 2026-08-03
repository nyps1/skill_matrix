import bcrypt
from app import create_app
from app.models.user import User
from app.extensions import db

def reset_all_passwords():
    app = create_app()
    with app.app_context():
        users = User.query.all()
        # Hash '1234' using bcrypt as expected by auth_service.py
        new_hash = bcrypt.hashpw('1234'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        for user in users:
            user.password_hash = new_hash
            
        db.session.commit()
        print(f"Successfully reset passwords for {len(users)} users to '1234'.")

if __name__ == '__main__':
    reset_all_passwords()
