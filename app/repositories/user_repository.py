from app.models.user import User
from app.models.skill import SkillCategory
from app.extensions import db
import bcrypt

class UserRepository:
    @staticmethod
    def get_by_username(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_by_id(user_id):
        return User.query.get(user_id)

    @staticmethod
    def get_all_engineers():
        return User.query.filter_by(role='engineer').all()

    @staticmethod
    def create_engineer(username, raw_password):
        hashed = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            username=username,
            password_hash=hashed,
            role='engineer'
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update_user_skills(user, skill_ids):
        # Fetch actual SkillCategory objects
        skills = SkillCategory.query.filter(SkillCategory.id.in_(skill_ids)).all()
        user.authorized_skills = skills
        db.session.commit()
        return user

    @staticmethod
    def update_password(user, raw_password):
        hashed = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.password_hash = hashed
        db.session.commit()
        return user

    @staticmethod
    def update_user(user):
        db.session.commit()
        return user
