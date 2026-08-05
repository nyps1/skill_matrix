from sqlalchemy.orm import joinedload
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
    def create_question(skill_id, q_type, content, options, answer, points=10):
        q = Question(
            skill_id=skill_id,
            type=q_type,
            content=content,
            options=options,
            answer=answer,
            points=points
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
    def update_question(q, skill_id, q_type, content, options, answer, points=10):
        q.skill_id = skill_id
        q.type = q_type
        q.content = content
        q.options = options
        q.answer = answer
        q.points = points
        db.session.commit()
        return q

    @staticmethod
    def update_skill_passing_score(skill_id, passing_score):
        skill = SkillCategory.query.get(skill_id)
        if skill:
            skill.passing_score = passing_score
            db.session.commit()
        return skill

    # Exam Sessions
    @staticmethod
    def get_session_by_id(session_id):
        return ExamSession.query.get(session_id)

    @staticmethod
    def get_latest_completed_sessions_per_skill(user_id):
        sessions = ExamSession.query.options(
            joinedload(ExamSession.answers).joinedload(ExamAnswer.question).joinedload(Question.skill)
        ).filter(ExamSession.user_id == user_id, ExamSession.status.in_(['submitted', 'graded']))\
            .order_by(ExamSession.submitted_at.desc()).all()
            
        latest_per_skill = {}
        for session in sessions:
            if session.skill_id not in latest_per_skill:
                latest_per_skill[session.skill_id] = session
        return list(latest_per_skill.values())

    @staticmethod
    def get_all_completed_sessions(user_id):
        return ExamSession.query.options(
            joinedload(ExamSession.answers).joinedload(ExamAnswer.question).joinedload(Question.skill)
        ).filter(ExamSession.user_id == user_id, ExamSession.status.in_(['submitted', 'graded']))\
            .order_by(ExamSession.submitted_at.asc()).all()

    @staticmethod
    def get_pending_sessions():
        return ExamSession.query.filter_by(status='submitted').all()

    @staticmethod
    def get_or_create_draft_session(user_id, skill_id):
        import sqlalchemy.exc
        session = ExamSession.query.filter_by(user_id=user_id, skill_id=skill_id, status='draft').first()
        if not session:
            try:
                session = ExamSession(user_id=user_id, skill_id=skill_id)
                db.session.add(session)
                db.session.commit()
                
                questions = Question.query.filter_by(skill_id=skill_id).all()
                for q in questions:
                    ans = ExamAnswer(session_id=session.id, question_id=q.id)
                    db.session.add(ans)
                db.session.commit()
            except sqlalchemy.exc.IntegrityError:
                # Caught a race condition where another draft was created simultaneously
                db.session.rollback()
                session = ExamSession.query.filter_by(user_id=user_id, skill_id=skill_id, status='draft').first()
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
        # Fetch all answers for this session in a single query
        answers = ExamAnswer.query.filter_by(session_id=session_id).all()
        answer_map = {ans.id: ans for ans in answers}
        
        for data in answers_data:
            ans_id = data.get('answer_id')
            if ans_id in answer_map:
                answer_map[ans_id].provided_answer = data.get('provided_answer')
        db.session.commit()

    @staticmethod
    def get_auto_gradable_answers(session_id):
        return ExamAnswer.query.join(Question).filter(
            ExamAnswer.session_id == session_id,
            Question.type == 'multiple_choice'
        ).all()
