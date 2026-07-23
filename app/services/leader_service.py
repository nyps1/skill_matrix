from app.repositories.user_repository import UserRepository
from app.repositories.assessment_repository import AssessmentRepository

class LeaderService:
    @staticmethod
    def get_dashboard_data():
        engineers = UserRepository.get_all_engineers()
        results = []
        
        for eng in engineers:
            latest_session = AssessmentRepository.get_latest_graded_session(eng.id)
            score = latest_session.total_score if latest_session else None
            
            skills_data = []
            if latest_session:
                skill_scores = {}
                for ans in latest_session.answers:
                    skill_name = ans.question.skill.name
                    if skill_name not in skill_scores:
                        skill_scores[skill_name] = {'total': 0, 'count': 0}
                    if ans.score is not None:
                        skill_scores[skill_name]['total'] += ans.score
                        skill_scores[skill_name]['count'] += 1
                
                for s_name, data in skill_scores.items():
                    if data['count'] > 0:
                        skills_data.append({'skill': s_name, 'score': data['total'] / data['count']})
                    
            results.append({
                'user': eng.to_dict(),
                'latest_score': score,
                'skills_radar': skills_data
            })
            
        return results

    @staticmethod
    def create_engineer(data):
        if not data.get('username') or not data.get('password'):
            raise ValueError('Missing fields')
            
        if UserRepository.get_by_username(data['username']):
            raise ValueError('Username already exists')
            
        return UserRepository.create_engineer(
            data['username'], 
            data['password']
        )

    @staticmethod
    def assign_skills_to_engineer(user_id, skill_ids):
        user = UserRepository.get_by_id(user_id)
        if not user or user.role != 'engineer':
            raise ValueError('Can only assign skills to engineers')
        
        return UserRepository.update_user_skills(user, skill_ids)

    @staticmethod
    def toggle_engineer_active(user_id):
        user = UserRepository.get_by_id(user_id)
        if not user or user.role != 'engineer':
            raise ValueError('Can only toggle engineers')
            
        user.is_active = not user.is_active
        return UserRepository.update_user(user)

    @staticmethod
    def reset_engineer_password(user_id, new_password):
        user = UserRepository.get_by_id(user_id)
        if not user or user.role != 'engineer':
            raise ValueError('Can only reset passwords for engineers')
            
        return UserRepository.update_password(user, new_password)

    @staticmethod
    def grade_exam(session_id, grades):
        session = AssessmentRepository.get_session_by_id(session_id)
        if not session or session.status != 'submitted':
            raise ValueError('Exam is not in submitted state')
            
        total_score = 0
        
        for g in grades:
            ans = AssessmentRepository.get_answer_by_id(g['answer_id'])
            if ans and ans.session_id == session.id:
                ans.score = g.get('score', 0)
                ans.feedback = g.get('feedback', '')
                AssessmentRepository.update_session(session)
                total_score += ans.score
                
        auto_graded = AssessmentRepository.get_auto_gradable_answers(session.id)
        for auto in auto_graded:
            if auto.score is not None:
                total_score += auto.score
                
        session.total_score = total_score
        session.status = 'graded'
        return AssessmentRepository.update_session(session)
