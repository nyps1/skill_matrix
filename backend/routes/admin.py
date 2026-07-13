import json
from flask import Blueprint, request, jsonify
from backend.models import db, User, SkillCategory, Question, ExamSession, ExamAnswer
from backend.utils.auth_middleware import token_required, admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard', methods=['GET'])
@token_required
@admin_required
def get_dashboard(current_user):
    # Get all engineers and their latest submitted exam scores
    engineers = User.query.filter_by(role='engineer').all()
    results = []
    
    for eng in engineers:
        latest_session = ExamSession.query.filter_by(user_id=eng.id, status='graded').order_by(ExamSession.submitted_at.desc()).first()
        score = latest_session.total_score if latest_session else None
        
        # Calculate skills radar data (average score per skill)
        skills_data = []
        if latest_session:
            # Group answers by skill_id
            skill_scores = {}
            for ans in latest_session.answers:
                skill_id = ans.question.skill_id
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
        
    return jsonify({'dashboard': results}), 200

@admin_bp.route('/skills', methods=['GET', 'POST'])
@token_required
@admin_required
def manage_skills(current_user):
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({'message': 'Skill name is required'}), 400
            
        new_skill = SkillCategory(name=data['name'], description=data.get('description', ''))
        db.session.add(new_skill)
        db.session.commit()
        return jsonify(new_skill.to_dict()), 201
        
    skills = SkillCategory.query.all()
    return jsonify([s.to_dict() for s in skills]), 200

@admin_bp.route('/questions', methods=['GET', 'POST'])
@token_required
@admin_required
def manage_questions(current_user):
    if request.method == 'POST':
        data = request.get_json()
        required_fields = ['skill_id', 'type', 'content', 'answer']
        if not all(k in data for k in required_fields):
            return jsonify({'message': 'Missing required fields'}), 400
            
        options = data.get('options')
        if options and isinstance(options, list):
            options = json.dumps(options)
            
        new_q = Question(
            skill_id=data['skill_id'],
            type=data['type'],
            content=data['content'],
            options=options,
            answer=data['answer']
        )
        db.session.add(new_q)
        db.session.commit()
        return jsonify(new_q.to_dict(include_answer=True)), 201
        
    questions = Question.query.all()
    return jsonify([q.to_dict(include_answer=True) for q in questions]), 200

@admin_bp.route('/exams/pending', methods=['GET'])
@token_required
@admin_required
def get_pending_exams(current_user):
    # Get exams that are submitted but not yet fully graded
    pending_sessions = ExamSession.query.filter_by(status='submitted').all()
    return jsonify([s.to_dict() for s in pending_sessions]), 200

@admin_bp.route('/exams/<int:session_id>/grade', methods=['POST'])
@token_required
@admin_required
def grade_exam(current_user, session_id):
    session = ExamSession.query.get_or_404(session_id)
    if session.status != 'submitted':
        return jsonify({'message': 'Exam is not in submitted state'}), 400
        
    data = request.get_json()
    grades = data.get('grades', []) # list of {answer_id: 1, score: 10, feedback: 'good'}
    
    total_score = 0
    for g in grades:
        ans = ExamAnswer.query.get(g['answer_id'])
        if ans and ans.session_id == session.id:
            ans.score = g.get('score', 0)
            ans.feedback = g.get('feedback', '')
            total_score += ans.score
            
    # Also sum auto-graded scores
    auto_graded = ExamAnswer.query.join(Question).filter(
        ExamAnswer.session_id == session.id,
        Question.type == 'multiple_choice'
    ).all()
    
    for auto in auto_graded:
        if auto.score is not None:
            total_score += auto.score
            
    session.total_score = total_score
    session.status = 'graded'
    db.session.commit()
    
    return jsonify({'message': 'Exam graded successfully', 'session': session.to_dict()}), 200
