from flask import Blueprint, request, jsonify
from app.services.assessment_service import AssessmentService
from app.repositories.assessment_repository import AssessmentRepository
from app.utils.auth_middleware import token_required

assessment_bp = Blueprint('assessment', __name__)

@assessment_bp.route('/skills', methods=['GET', 'POST'])
@token_required
def manage_skills(current_user):
    if request.method == 'POST':
        data = request.get_json()
        try:
            skill = AssessmentService.create_skill(data, current_user)
            return jsonify(skill.to_dict()), 201
        except ValueError as e:
            return jsonify({'message': str(e)}), 403
            
    skills = AssessmentRepository.get_all_skills()
    return jsonify([s.to_dict() for s in skills]), 200

@assessment_bp.route('/questions', methods=['GET', 'POST'])
@token_required
def manage_questions(current_user):
    if request.method == 'POST':
        data = request.get_json()
        try:
            q = AssessmentService.create_question(data, current_user)
            return jsonify(q.to_dict(include_answer=True)), 201
        except ValueError as e:
            return jsonify({'message': str(e)}), 403
            
    if current_user.role != 'leader' and not current_user.authorized_skills:
        return jsonify({'message': 'Not authorized'}), 403
        
    questions = AssessmentRepository.get_all_questions()
    return jsonify([q.to_dict(include_answer=True) for q in questions]), 200

@assessment_bp.route('/questions/<int:question_id>', methods=['PUT'])
@token_required
def update_question(current_user, question_id):
    data = request.get_json()
    try:
        q = AssessmentService.update_question(question_id, data, current_user)
        return jsonify(q.to_dict(include_answer=True)), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 403

@assessment_bp.route('/available_exams', methods=['GET'])
@token_required
def get_available_exams(current_user):
    # Allow both engineers and leaders to view available exams
    
    available = AssessmentService.get_available_exams(current_user)
    return jsonify(available), 200

@assessment_bp.route('/exams/start', methods=['POST'])
@token_required
def start_exam(current_user):
    # Allow both engineers and leaders to start exams for testing
    data = request.get_json()
    skill_id = data.get('skill_id')
    if not skill_id:
        return jsonify({'message': 'skill_id is required'}), 400
        
    try:
        session = AssessmentService.start_or_resume_exam(current_user.id, skill_id)
        return jsonify({'session_id': session.id, 'status': session.status}), 201
    except ValueError as e:
        return jsonify({'message': str(e)}), 400

@assessment_bp.route('/exams/<int:session_id>/questions', methods=['GET'])
@token_required
def get_exam_questions(current_user, session_id):
    try:
        questions = AssessmentService.get_exam_questions(session_id, current_user.id)
        return jsonify(questions), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 403

@assessment_bp.route('/exams/<int:session_id>/autosave', methods=['POST'])
@token_required
def autosave_exam(current_user, session_id):
    data = request.get_json()
    try:
        AssessmentService.autosave_exam(session_id, current_user.id, data.get('answers', []))
        return jsonify({'message': 'Autosaved successfully'}), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 400

@assessment_bp.route('/exams/<int:session_id>/submit', methods=['POST'])
@token_required
def submit_exam(current_user, session_id):
    try:
        session = AssessmentService.submit_exam(session_id, current_user.id)
        return jsonify({'message': 'Exam submitted', 'session_id': session.id}), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 400

@assessment_bp.route('/my-dashboard', methods=['GET'])
@token_required
def my_dashboard(current_user):
    """Return the current engineer's own skill radar data."""
    sessions = AssessmentRepository.get_latest_completed_sessions_per_skill(current_user.id)
    
    skills_data = []
    total_score_sum = 0
    total_score_count = 0
    latest_submitted_at = None

    for session in sessions:
        if session.total_score is not None:
            total_score_sum += session.total_score
            total_score_count += 1
            
        # Keep track of the absolute latest submission time
        if session.submitted_at:
            if latest_submitted_at is None or session.submitted_at > latest_submitted_at:
                latest_submitted_at = session.submitted_at

        # Calculate score for this skill session
        skill_name = session.skill.name if session.skill else 'Unknown'
        skill_score_sum = 0
        skill_ans_count = 0
        for ans in session.answers:
            if ans.score is not None:
                skill_score_sum += ans.score
                skill_ans_count += 1
                
        if skill_ans_count > 0:
            skills_data.append({
                'skill': skill_name,
                'score': round(skill_score_sum / skill_ans_count, 1)
            })

    overall_score = round(total_score_sum / total_score_count, 1) if total_score_count > 0 else None
    
    return jsonify({
        'user': current_user.to_dict(),
        'latest_score': overall_score,
        'submitted_at': latest_submitted_at.isoformat() if latest_submitted_at else None,
        'skills_radar': skills_data
    }), 200

