import os
import bcrypt
from flask import Flask
from app.extensions import db

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Configure Database
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'skill_assessment.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Extensions
    db.init_app(app)
    
    # Enable SQLite WAL Mode for concurrency
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
        
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

    # Register API Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.leader_routes import leader_bp
    from app.routes.assessment_routes import assessment_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(leader_bp, url_prefix='/api/admin')
    app.register_blueprint(assessment_bp, url_prefix='/api/assessment')

    # --- Page Routes (Multi-Page Application) ---
    from flask import render_template

    @app.route('/')
    def index():
        return render_template('login.html')

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/dashboard')
    def dashboard_page():
        return render_template('dashboard.html')

    @app.route('/skills')
    def skills_page():
        return render_template('skills.html')

    @app.route('/users')
    def users_page():
        return render_template('users.html')

    @app.route('/questions')
    def questions_page():
        return render_template('questions.html')

    @app.route('/engineer')
    def engineer_page():
        return render_template('engineer.html')

    @app.route('/engineer/assessments')
    def engineer_assessments_page():
        return render_template('engineer_assessments.html')

    @app.route('/engineer/questions')
    def engineer_questions_page():
        return render_template('engineer_questions.html')

    @app.route('/exam')
    def exam_page():
        return render_template('exam.html')

    # Static file fallback
    @app.route('/<path:path>')
    def serve_static(path):
        return app.send_static_file(path)

    return app

def setup_database(app):
    from app.models.user import User
    from app.models.assessment import ExamSession
    with app.app_context():
        db.create_all()
        # Create unique partial index to prevent race conditions (only 1 draft session per user)
        db.session.execute(db.text("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_draft_session ON exam_sessions (user_id) WHERE status = 'draft'"))
        db.session.commit()
        
        if not User.query.filter_by(username='leader').first():
            hashed = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            leader_user = User(username='leader', password_hash=hashed, role='leader')
            db.session.add(leader_user)
            
            eng_hashed = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            eng_user = User(username='engineer1', password_hash=eng_hashed, role='engineer')
            db.session.add(eng_user)
            
            db.session.commit()
            print("Database initialized with seed users: leader/password, engineer1/password")
