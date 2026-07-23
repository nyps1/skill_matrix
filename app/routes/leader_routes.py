from flask import Blueprint, request, jsonify
from app.services.leader_service import LeaderService
from app.repositories.user_repository import UserRepository
from app.utils.auth_middleware import token_required, leader_required

leader_bp = Blueprint('leader', __name__)

@leader_bp.route('/dashboard', methods=['GET'])
@token_required
@leader_required
def get_dashboard(current_user):
    data = LeaderService.get_dashboard_data()
    return jsonify({'dashboard': data}), 200

@leader_bp.route('/users', methods=['GET'])
@token_required
@leader_required
def get_users(current_user):
    engineers = UserRepository.get_all_engineers()
    return jsonify([u.to_dict() for u in engineers]), 200

@leader_bp.route('/users', methods=['POST'])
@token_required
@leader_required
def create_user(current_user):
    data = request.get_json()
    try:
        user = LeaderService.create_engineer(data)
        return jsonify(user.to_dict()), 201
    except ValueError as e:
        return jsonify({'message': str(e)}), 400

@leader_bp.route('/users/<int:user_id>/permissions', methods=['PUT'])
@token_required
@leader_required
def update_permissions(current_user, user_id):
    data = request.get_json()
    skill_ids = data.get('skill_ids', [])
    try:
        user = LeaderService.assign_skills_to_engineer(user_id, skill_ids)
        return jsonify(user.to_dict()), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 400

@leader_bp.route('/users/<int:user_id>/toggle-active', methods=['PUT'])
@token_required
@leader_required
def toggle_active(current_user, user_id):
    try:
        user = LeaderService.toggle_engineer_active(user_id)
        return jsonify(user.to_dict()), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 400

@leader_bp.route('/users/<int:user_id>/password', methods=['PUT'])
@token_required
@leader_required
def reset_password(current_user, user_id):
    data = request.get_json()
    new_password = data.get('new_password')
    if not new_password:
        return jsonify({'message': 'New password is required'}), 400
        
    try:
        LeaderService.reset_engineer_password(user_id, new_password)
        return jsonify({'message': 'Password reset successfully'}), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 400

@leader_bp.route('/exams/<int:session_id>/grade', methods=['POST'])
@token_required
@leader_required
def grade_exam(current_user, session_id):
    data = request.get_json()
    try:
        session = LeaderService.grade_exam(session_id, data.get('grades', []))
        return jsonify({'message': 'Exam graded successfully', 'session': session.to_dict()}), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
