from functools import wraps
from flask import request, jsonify
from app.services.auth_service import AuthService

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
            
        current_user = AuthService.decode_token(token)
        if not current_user:
            return jsonify({'message': 'Token is invalid or expired!'}), 401
            
        if not current_user.is_active:
            return jsonify({'message': 'Account is deactivated'}), 403
            
        return f(current_user, *args, **kwargs)
    return decorated

def leader_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'leader':
            return jsonify({'message': 'Leader privileges required!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated
