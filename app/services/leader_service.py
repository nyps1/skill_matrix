from app.repositories.user_repository import UserRepository
from app.repositories.assessment_repository import AssessmentRepository

class LeaderService:
    @staticmethod
    def get_dashboard_data():
        engineers = UserRepository.get_all_engineers()
        results = []
        
        for eng in engineers:
            all_sessions = AssessmentRepository.get_all_completed_sessions(eng.id)
            
            trends_by_skill = {}
            latest_per_skill_map = {}
            
            for session in all_sessions:
                skill_name = session.skill.name if session.skill else 'Unknown'
                
                skill_score_sum = 0
                skill_ans_count = 0
                for ans in session.answers:
                    if ans.score is not None:
                        skill_score_sum += ans.score
                        skill_ans_count += 1
                        
                session_avg_score = round(skill_score_sum / skill_ans_count, 1) if skill_ans_count > 0 else 0
                
                if skill_name not in trends_by_skill:
                    trends_by_skill[skill_name] = []
                    
                date_str = session.submitted_at.strftime('%Y-%m-%d %H:%M') if session.submitted_at else 'Unknown'
                trends_by_skill[skill_name].append({
                    'date': date_str,
                    'score': session_avg_score
                })
                
                latest_per_skill_map[skill_name] = {
                    'session': session,
                    'avg_score': session_avg_score
                }
                
            skills_data = []
            total_score_sum = 0
            total_score_count = 0
            
            for skill_name, data in latest_per_skill_map.items():
                skills_data.append({'skill': skill_name, 'score': data['avg_score']})
                if data['session'].total_score is not None:
                    total_score_sum += data['session'].total_score
                    total_score_count += 1
            
            overall_score = round(total_score_sum / total_score_count, 1) if total_score_count > 0 else None
            
            results.append({
                'user': eng.to_dict(),
                'latest_score': overall_score,
                'skills_radar': skills_data,
                'historical_trends': trends_by_skill
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
