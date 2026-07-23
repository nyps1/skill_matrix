from app.models.assessment import Question, ExamSession, ExamAnswer
from app.models.skill import SkillCategory
from app.extensions import db

class AssessmentRepository:
    # Skills
    @staticmethod
    def get_all_skills():
        return SkillCategory.query.all()

    @staticmethod
    def create_skill(name, description=''):
        skill = SkillCategory(name=name, description=description)
        db.session.add(skill)
        db.session.commit()
        return skill

    # Questions
    @staticmethod
    def create_question(skill_id, q_type, content, options, answer):
        q = Question(
            skill_id=skill_id,
            type=q_type,
            content=content,
            options=options,
            answer=answer
        )
        db.session.add(q)
        db.session.commit()
        return q

    @staticmethod
    def get_all_questions():
        return Question.query.all()

    @staticmethod
    def get_question_by_id(question_id):
        return Question.query.get(question_id)

    @staticmethod
    def update_question(q, skill_id, q_type, content, options, answer):
        q.skill_id = skill_id
        q.type = q_type
        q.content = content
        q.options = options
        q.answer = answer
        db.session.commit()
        return q

    # Exam Sessions
    @staticmethod
    def get_session_by_id(session_id):
        return ExamSession.query.get(session_id)

    @staticmethod
    def get_latest_graded_session(user_id):
        return ExamSession.query.filter_by(user_id=user_id, status='graded')\
            .order_by(ExamSession.submitted_at.desc()).first()

    @staticmethod
    def get_pending_sessions():
        return ExamSession.query.filter_by(status='submitted').all()

    @staticmethod
    def get_or_create_draft_session(user_id):
        session = ExamSession.query.filter_by(user_id=user_id, status='draft').first()
        if not session:
            session = ExamSession(user_id=user_id)
            db.session.add(session)
            db.session.commit()
            
            questions = Question.query.all()
            for q in questions:
                ans = ExamAnswer(session_id=session.id, question_id=q.id)
                db.session.add(ans)
            db.session.commit()
        return session

    @staticmethod
    def update_session(session):
        db.session.commit()
        return session

    # Exam Answers
    @staticmethod
    def get_answer_by_id(answer_id):
        return ExamAnswer.query.get(answer_id)

    @staticmethod
    def update_answers(session_id, answers_data):
        for data in answers_data:
            ans = ExamAnswer.query.get(data['answer_id'])
            if ans and ans.session_id == session_id:
                ans.provided_answer = data['provided_answer']
        db.session.commit()

    @staticmethod
    def get_auto_gradable_answers(session_id):
        return ExamAnswer.query.join(Question).filter(
            ExamAnswer.session_id == session_id,
            Question.type == 'multiple_choice'
        ).all()
