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

@assessment_bp.route('/exams/start', methods=['POST'])
@token_required
def start_exam(current_user):
    if current_user.role != 'engineer':
        return jsonify({'message': 'Only engineers can take exams'}), 403
        
    session = AssessmentService.start_or_resume_exam(current_user.id)
    return jsonify({'session_id': session.id, 'status': session.status}), 201

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
    latest_session = AssessmentRepository.get_latest_graded_session(current_user.id)
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
                skills_data.append({
                    'skill': s_name,
                    'score': round(data['total'] / data['count'], 1)
                })

    submitted_at = None
    if latest_session and latest_session.submitted_at:
        submitted_at = latest_session.submitted_at.isoformat()

    return jsonify({
        'user': current_user.to_dict(),
        'latest_score': score,
        'submitted_at': submitted_at,
        'skills_radar': skills_data
    }), 200

