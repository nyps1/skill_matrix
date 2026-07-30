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
    from app.models.skill import SkillCategory
    from app.models.assessment import Question, ExamSession, ExamAnswer
    import json
    
    with app.app_context():
        # Because we added skill_id, we just drop and recreate the test DB
        db.drop_all()
        db.create_all()
        # Create unique partial index to prevent race conditions (only 1 draft session per user per skill)
        db.session.execute(db.text("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_draft_session ON exam_sessions (user_id, skill_id) WHERE status = 'draft'"))
        db.session.commit()
        
        if not User.query.filter_by(username='leader').first():
            hashed = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Users
            leader = User(username='leader', password_hash=hashed, role='leader')
            eng_a = User(username='eng_a', password_hash=hashed, role='engineer')
            eng_b = User(username='eng_b', password_hash=hashed, role='engineer')
            eng_c = User(username='eng_c', password_hash=hashed, role='engineer')
            eng_d = User(username='eng_d', password_hash=hashed, role='engineer', is_active=False)
            db.session.add_all([leader, eng_a, eng_b, eng_c, eng_d])
            db.session.commit()
            
            # Skills
            python = SkillCategory(name='Python', description='Python Programming')
            vue = SkillCategory(name='Vue.js', description='Frontend Framework')
            docker = SkillCategory(name='Docker', description='Containerization')
            ml = SkillCategory(name='Machine Learning', description='AI/ML')
            db.session.add_all([python, vue, docker, ml])
            db.session.commit()
            
            # Authorizations
            eng_a.authorized_skills.append(python)
            eng_b.authorized_skills.append(vue)
            db.session.commit()
            
            # Questions
            options = json.dumps(["A", "B", "C", "D"])
            for i in range(5):
                db.session.add(Question(skill_id=python.id, type='multiple_choice', content=f'Python Q{i+1}', options=options, answer='A'))
            for i in range(3):
                db.session.add(Question(skill_id=vue.id, type='multiple_choice', content=f'Vue Q{i+1}', options=options, answer='B'))
            db.session.add(Question(skill_id=docker.id, type='multiple_choice', content='Docker Q1', options=options, answer='C'))
            # ML has 0 questions
            db.session.commit()
            
            # Draft Sessions
            # eng_a Vue draft (2 out of 3 answered)
            vue_draft = ExamSession(user_id=eng_a.id, skill_id=vue.id, status='draft')
            db.session.add(vue_draft)
            db.session.commit()
            vue_qs = Question.query.filter_by(skill_id=vue.id).all()
            for i, q in enumerate(vue_qs):
                db.session.add(ExamAnswer(session_id=vue_draft.id, question_id=q.id, provided_answer='B' if i < 2 else None))
                
            # eng_a Docker draft (0 answered)
            doc_draft = ExamSession(user_id=eng_a.id, skill_id=docker.id, status='draft')
            db.session.add(doc_draft)
            db.session.commit()
            db.session.add(ExamAnswer(session_id=doc_draft.id, question_id=Question.query.filter_by(skill_id=docker.id).first().id))
            
            # Graded & Submitted Sessions
            # eng_c Python graded
            py_graded = ExamSession(user_id=eng_c.id, skill_id=python.id, status='graded', total_score=40)
            db.session.add(py_graded)
            db.session.commit()
            for q in Question.query.filter_by(skill_id=python.id).all():
                db.session.add(ExamAnswer(session_id=py_graded.id, question_id=q.id, provided_answer='A', score=8))
                
            # eng_c Vue submitted
            vue_sub = ExamSession(user_id=eng_c.id, skill_id=vue.id, status='submitted')
            db.session.add(vue_sub)
            db.session.commit()
            for q in vue_qs:
                db.session.add(ExamAnswer(session_id=vue_sub.id, question_id=q.id, provided_answer='A'))

            db.session.commit()
            print("Database initialized with comprehensive seed data for various scenarios.")
