from app.repositories.assessment_repository import AssessmentRepository
from datetime import datetime
import json

class AssessmentService:
    @staticmethod
    def create_skill(data, current_user):
        if current_user.role != 'leader':
            raise ValueError('Only leader can create skills')
        if not data.get('name'):
            raise ValueError('Skill name is required')
        return AssessmentRepository.create_skill(data['name'], data.get('description', ''))

    @staticmethod
    def create_question(data, current_user):
        required_fields = ['skill_id', 'type', 'content', 'answer']
        if not all(k in data for k in required_fields):
            raise ValueError('Missing required fields')

        # Permission check
        skill_id = int(data['skill_id'])
        if current_user.role != 'leader':
            authorized = [s.id for s in current_user.authorized_skills]
            if skill_id not in authorized:
                raise ValueError('Not authorized to create questions for this skill')
            
        options = data.get('options')
        if options and isinstance(options, list):
            options = json.dumps(options)
            
        return AssessmentRepository.create_question(
            skill_id,
            data['type'],
            data['content'],
            options,
            data['answer']
        )

    @staticmethod
    def update_question(question_id, data, current_user):
        q = AssessmentRepository.get_question_by_id(question_id)
        if not q:
            raise ValueError('Question not found')

        required_fields = ['skill_id', 'type', 'content', 'answer']
        if not all(k in data for k in required_fields):
            raise ValueError('Missing required fields')

        skill_id = int(data['skill_id'])
        if current_user.role != 'leader':
            authorized = [s.id for s in current_user.authorized_skills]
            if skill_id not in authorized or q.skill_id not in authorized:
                raise ValueError('Not authorized to edit questions for this skill')

        options = data.get('options')
        if options and isinstance(options, list):
            options = json.dumps(options)

        return AssessmentRepository.update_question(
            q,
            skill_id,
            data['type'],
            data['content'],
            options,
            data['answer']
        )

    @staticmethod
    def start_or_resume_exam(user_id):
        return AssessmentRepository.get_or_create_draft_session(user_id)

    @staticmethod
    def get_exam_questions(session_id, user_id):
        session = AssessmentRepository.get_session_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError('Session not found')
            
        questions = []
        for ans in session.answers:
            questions.append({
                'answer_id': ans.id,
                'question': ans.question.to_dict(),
                'provided_answer': ans.provided_answer
            })
        return questions

    @staticmethod
    def autosave_exam(session_id, user_id, answers_data):
        session = AssessmentRepository.get_session_by_id(session_id)
        if not session or session.user_id != user_id or session.status != 'draft':
            raise ValueError('Invalid session')
            
        AssessmentRepository.update_answers(session_id, answers_data)

    @staticmethod
    def submit_exam(session_id, user_id):
        session = AssessmentRepository.get_session_by_id(session_id)
        if not session or session.user_id != user_id or session.status != 'draft':
            raise ValueError('Invalid session')
            
        auto_graded = AssessmentRepository.get_auto_gradable_answers(session.id)
        for ans in auto_graded:
            if ans.provided_answer and ans.provided_answer.strip() == ans.question.answer.strip():
                ans.score = 10
            else:
                ans.score = 0
                
        session.status = 'submitted'
        session.submitted_at = datetime.utcnow()
        AssessmentRepository.update_session(session)
        return session
