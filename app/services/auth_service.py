import jwt
import bcrypt
from datetime import datetime, timedelta
from app.repositories.user_repository import UserRepository
import os

class AuthService:
    SECRET_KEY = 'your-secret-key-for-jwt-keep-it-secret' # Ideally from config

    @staticmethod
    def authenticate(username, password):
        user = UserRepository.get_by_username(username)
        if not user:
            return None, 'Invalid credentials'
        
        if not user.is_active:
            return None, 'Account is deactivated'

        if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, AuthService.SECRET_KEY, algorithm='HS256')
            return token, None
            
        return None, 'Invalid credentials'

    @staticmethod
    def decode_token(token):
        try:
            data = jwt.decode(token, AuthService.SECRET_KEY, algorithms=['HS256'])
            user = UserRepository.get_by_id(data['user_id'])
            return user
        except:
            return None

    @staticmethod
    def change_my_password(user_id, current_password, new_password):
        user = UserRepository.get_by_id(user_id)
        if not user:
            raise ValueError('User not found')
        if not bcrypt.checkpw(current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
            raise ValueError('Incorrect current password')
        return UserRepository.update_password(user, new_password)
