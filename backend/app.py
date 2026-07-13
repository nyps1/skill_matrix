import os
import bcrypt
from flask import Flask, jsonify
from flask_cors import CORS
from backend.models import db, User

def create_app():
    app = Flask(__name__)
    
    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'skill_assessment.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'super-secret-development-key' # In production, use env var
    
    CORS(app)
    db.init_app(app)
    
    # Register Blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.admin import admin_bp
    from backend.routes.assessment import assessment_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(assessment_bp, url_prefix='/api/assessment')
    
    # Error handling
    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error=str(e)), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify(error=str(e)), 500
        
    return app

def setup_database(app):
    with app.app_context():
        db.create_all()
        # Seed initial admin user if not exists
        if not User.query.filter_by(username='admin').first():
            hashed = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin_user = User(username='admin', password_hash=hashed, role='admin')
            db.session.add(admin_user)
            
            # Seed a test engineer as well
            eng_hashed = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            eng_user = User(username='engineer1', password_hash=eng_hashed, role='engineer')
            db.session.add(eng_user)
            
            db.session.commit()
            print("Database initialized with seed users: admin/password, engineer1/password")

if __name__ == '__main__':
    app = create_app()
    setup_database(app)
    app.run(debug=True, port=5000)
