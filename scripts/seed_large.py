import random
import bcrypt
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.skill import SkillCategory
from app.models.assessment import Question, ExamSession, ExamAnswer
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def seed_large_data():
    app = create_app()
    with app.app_context():
        print("Starting large data seed...")

        # 1. Create 10 Skills
        skill_names = ["React.js", "Vue.js", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD", "TypeScript", "Node.js"]
        skills = []
        for name in skill_names:
            # Check if exists
            s = SkillCategory.query.filter_by(name=name).first()
            if not s:
                s = SkillCategory(name=name, description=f"Assessment for {name}")
                db.session.add(s)
            skills.append(s)
        db.session.commit()
        print(f"Ensured {len(skills)} skills exist.")

        # 2. Create Questions for each skill
        for s in skills:
            q_count = Question.query.filter_by(skill_id=s.id).count()
            if q_count < 3:
                for i in range(3 - q_count):
                    q = Question(
                        skill_id=s.id,
                        type="multiple_choice",
                        content=f"Sample question {i+1} for {s.name}?",
                        options='["Option A", "Option B", "Option C", "Option D"]',
                        answer="Option A"
                    )
                    db.session.add(q)
        db.session.commit()
        print("Ensured 3 questions per skill.")

        # 3. Create 100 Engineers
        engineers = []
        for i in range(1, 101):
            username = f"engineer_{i:03d}"
            u = User.query.filter_by(username=username).first()
            if not u:
                pwd_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                u = User(
                    username=username,
                    password_hash=pwd_hash,
                    role='engineer',
                    is_active=True
                )
                db.session.add(u)
            engineers.append(u)
        db.session.commit()
        print(f"Ensured {len(engineers)} engineers exist.")

        # 4. Create Exam Records (At least 3 skills per engineer)
        print("Creating exam records. This may take a moment...")
        for u in engineers:
            # Check how many completed sessions this user has
            completed_count = ExamSession.query.filter_by(user_id=u.id, status='submitted').count()
            if completed_count >= 3:
                continue
                
            # Assign random skills
            assigned_skills = random.sample(skills, 3)
            # Give permissions
            for s in assigned_skills:
                if s not in u.authorized_skills:
                    u.authorized_skills.append(s)
            db.session.commit()
            
            for s in assigned_skills:
                # Check if session exists
                sess = ExamSession.query.filter_by(user_id=u.id, skill_id=s.id, status='submitted').first()
                if not sess:
                    # Random time in the last 30 days
                    random_days = random.randint(1, 30)
                    dt = datetime.utcnow() - timedelta(days=random_days)
                    
                    sess = ExamSession(
                        user_id=u.id,
                        skill_id=s.id,
                        status='submitted',
                        started_at=dt - timedelta(minutes=30),
                        submitted_at=dt
                    )
                    db.session.add(sess)
                    db.session.flush() # Get ID
                    
                    # Create answers
                    skill_questions = Question.query.filter_by(skill_id=s.id).all()
                    total_score = 0
                    for q in skill_questions:
                        # randomly decide if correct
                        is_correct = random.choice([True, False, True]) # 66% chance of correct
                        score = 10 if is_correct else 0
                        total_score += score
                        ans = ExamAnswer(
                            session_id=sess.id,
                            question_id=q.id,
                            provided_answer=q.answer if is_correct else "Option B",
                            score=score
                        )
                        db.session.add(ans)
                    sess.total_score = total_score
            db.session.commit()
            
        print("All test data seeded successfully!")

if __name__ == '__main__':
    seed_large_data()
