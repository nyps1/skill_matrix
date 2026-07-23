from app.extensions import db
from datetime import datetime
import json

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill_categories.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False) # 'multiple_choice' or 'open_ended'
    content = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=True) # JSON string for multiple_choice
    answer = db.Column(db.Text, nullable=False)

    skill = db.relationship('SkillCategory', backref=db.backref('questions', lazy=True))

    def to_dict(self, include_answer=False):
        data = {
            'id': self.id,
            'skill_id': self.skill_id,
            'skill_name': self.skill.name if self.skill else None,
            'type': self.type,
            'content': self.content,
            'options': json.loads(self.options) if self.options else None
        }
        if include_answer:
            data['answer'] = self.answer
        return data

class ExamSession(db.Model):
    __tablename__ = 'exam_sessions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='draft') # 'draft', 'submitted', 'graded'
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)
    total_score = db.Column(db.Integer, nullable=True)

    user = db.relationship('User', backref=db.backref('exam_sessions', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'total_score': self.total_score
        }

class ExamAnswer(db.Model):
    __tablename__ = 'exam_answers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.Integer, db.ForeignKey('exam_sessions.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    provided_answer = db.Column(db.Text, nullable=True)
    score = db.Column(db.Integer, nullable=True)
    feedback = db.Column(db.Text, nullable=True)

    session = db.relationship('ExamSession', backref=db.backref('answers', lazy=True, cascade="all, delete-orphan"))
    question = db.relationship('Question')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'question_id': self.question_id,
            'provided_answer': self.provided_answer,
            'score': self.score,
            'feedback': self.feedback
        }
