from app.extensions import db

user_skill_permissions = db.Table('user_skill_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skill_categories.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='engineer') # 'leader' or 'engineer'
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    authorized_skills = db.relationship('SkillCategory', secondary=user_skill_permissions, lazy='subquery',
        backref=db.backref('authorized_users', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'is_active': self.is_active,
            'authorized_skills': [s.id for s in self.authorized_skills]
        }
