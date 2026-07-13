import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from backend.models import db, Question, ExamSession, ExamAnswer
from backend.utils.auth_middleware import token_required

assessment_bp = Blueprint('assessment', __name__)

@assessment_bp.route('/exams/start', methods=['POST'])
@token_required
def start_exam(current_user):
    if current_user.role != 'engineer':
        return jsonify({'message': 'Only engineers can take exams'}), 403
        
    # Check if there's an ongoing draft
    existing_draft = ExamSession.query.filter_by(user_id=current_user.id, status='draft').first()
    if existing_draft:
        return jsonify({'message': 'Draft recovered', 'session_id': existing_draft.id}), 200
        
    # Create new session
    new_session = ExamSession(user_id=current_user.id, status='draft')
    db.session.add(new_session)
    db.session.commit()
    
    # Pre-populate answers for all active questions
    questions = Question.query.all()
    for q in questions:
        ans = ExamAnswer(session_id=new_session.id, question_id=q.id)
        db.session.add(ans)
    db.session.commit()
    
    return jsonify({'message': 'Exam started', 'session_id': new_session.id}), 201

@assessment_bp.route('/exams/<int:session_id>/questions', methods=['GET'])
@token_required
def get_exam_questions(current_user, session_id):
    session = ExamSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    
    answers = ExamAnswer.query.filter_by(session_id=session.id).all()
    result = []
    for ans in answers:
        q_dict = ans.question.to_dict(include_answer=False)
        result.append({
            'answer_id': ans.id,
            'question': q_dict,
            'provided_answer': ans.provided_answer
        })
        
    return jsonify(result), 200

@assessment_bp.route('/exams/<int:session_id>/autosave', methods=['PUT'])
@token_required
def autosave_exam(current_user, session_id):
    session = ExamSession.query.filter_by(id=session_id, user_id=current_user.id, status='draft').first_or_404()
    
    data = request.get_json()
    answers_data = data.get('answers', []) # list of {answer_id: 1, provided_answer: 'A'}
    
    for a in answers_data:
        ans = ExamAnswer.query.filter_by(id=a['answer_id'], session_id=session.id).first()
        if ans:
            ans.provided_answer = a.get('provided_answer')
            
    db.session.commit()
    return jsonify({'message': 'Draft autosaved successfully'}), 200

@assessment_bp.route('/exams/<int:session_id>/submit', methods=['POST'])
@token_required
def submit_exam(current_user, session_id):
    session = ExamSession.query.filter_by(id=session_id, user_id=current_user.id, status='draft').first_or_404()
    
    # Auto-grade multiple choice questions
    answers = ExamAnswer.query.filter_by(session_id=session.id).all()
    for ans in answers:
        q = ans.question
        if q.type == 'multiple_choice':
            if ans.provided_answer and ans.provided_answer.strip() == q.answer.strip():
                ans.score = 10.0 # Standard 10 points for multiple choice
            else:
                ans.score = 0.0
                
    session.status = 'submitted'
    session.submitted_at = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify({'message': 'Exam submitted successfully'}), 200
