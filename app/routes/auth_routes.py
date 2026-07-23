from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from app.utils.auth_middleware import token_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing fields'}), 400

    token, error = AuthService.authenticate(data['username'], data['password'])
    
    if error:
        return jsonify({'message': error}), 401 if error == 'Invalid credentials' else 403

    user = AuthService.decode_token(token)
    return jsonify({
        'token': token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_me(current_user):
    return jsonify({'user': current_user.to_dict()}), 200

@auth_bp.route('/password', methods=['PUT'])
@token_required
def change_password(current_user):
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    if not current_password or not new_password:
        return jsonify({'message': 'Current password and new password are required'}), 400
        
    try:
        AuthService.change_my_password(current_user.id, current_password, new_password)
        return jsonify({'message': 'Password changed successfully'}), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 400

