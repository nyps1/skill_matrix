import requests
import json
import uuid

BASE_URL = 'http://127.0.0.1:5000'

def test_full_flow():
    print("--- Starting Full System Test Flow ---")
    session = requests.Session()
    
    # 1. Login as Leader
    res = session.post(f"{BASE_URL}/api/auth/login", json={"username": "leader", "password": "password"})
    assert res.status_code == 200, f"Leader login failed: {res.text}"
    token = res.json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    print("1. Leader login successful.")
    
    # 2. Create a new skill
    skill_name = f"Test Skill {uuid.uuid4().hex[:6]}"
    res = session.post(f"{BASE_URL}/api/assessment/skills", json={"name": skill_name, "description": "Auto test"}, headers=headers)
    assert res.status_code == 201, f"Create skill failed: {res.text}"
    skill_id = res.json()['id']
    print(f"2. Skill '{skill_name}' created (ID: {skill_id}).")
    
    # 3. Create a question for the skill
    q_data = {
        "skill_id": skill_id,
        "type": "multiple_choice",
        "content": "What is 2+2?",
        "options": ["3", "4", "5", "6"],
        "answer": "B"
    }
    res = session.post(f"{BASE_URL}/api/assessment/questions", json=q_data, headers=headers)
    assert res.status_code == 201, f"Create question failed: {res.text}"
    print("3. Question created.")
    
    # 4. Create a new engineer
    eng_name = f"eng_{uuid.uuid4().hex[:6]}"
    res = session.post(f"{BASE_URL}/api/admin/users", json={"username": eng_name, "password": "password"}, headers=headers)
    assert res.status_code == 201, f"Create user failed: {res.text}"
    eng_id = res.json()['id']
    print(f"4. Engineer '{eng_name}' created (ID: {eng_id}).")
    
    # 5. Assign skill to engineer
    res = session.put(f"{BASE_URL}/api/admin/users/{eng_id}/permissions", json={"skill_ids": [skill_id]}, headers=headers)
    assert res.status_code == 200, f"Assign permission failed: {res.text}"
    print("5. Skill assigned to engineer.")
    
    # 6. Login as Engineer
    eng_session = requests.Session()
    res = eng_session.post(f"{BASE_URL}/api/auth/login", json={"username": eng_name, "password": "password"})
    assert res.status_code == 200, f"Engineer login failed: {res.text}"
    eng_token = res.json()['token']
    eng_headers = {'Authorization': f'Bearer {eng_token}'}
    print("6. Engineer login successful.")
    
    # 7. Check Available Exams
    res = eng_session.get(f"{BASE_URL}/api/assessment/available_exams", headers=eng_headers)
    assert res.status_code == 200, f"Get exams failed: {res.text}"
    exams = res.json()
    assert any(e['skill_id'] == skill_id for e in exams), "Newly created exam not found in available exams"
    print("7. Available exams checked.")
    
    # 8. Start Exam
    res = eng_session.post(f"{BASE_URL}/api/assessment/exams/start", json={"skill_id": skill_id}, headers=eng_headers)
    assert res.status_code == 201, f"Start exam failed: {res.text}"
    session_id = res.json()['session_id']
    print(f"8. Exam started (Session ID: {session_id}).")
    
    # 9. Get Questions & Autosave & Submit
    res = eng_session.get(f"{BASE_URL}/api/assessment/exams/{session_id}/questions", headers=eng_headers)
    assert res.status_code == 200, f"Get exam questions failed: {res.text}"
    questions = res.json()
    answer_id = questions[0]['answer_id']
    
    # Autosave
    autosave_data = {"answers": [{"answer_id": answer_id, "provided_answer": "B"}]}
    res = eng_session.post(f"{BASE_URL}/api/assessment/exams/{session_id}/autosave", json=autosave_data, headers=eng_headers)
    assert res.status_code == 200, f"Autosave failed: {res.text}"
    print("9. Exam autosaved.")
    
    # Submit
    res = eng_session.post(f"{BASE_URL}/api/assessment/exams/{session_id}/submit", headers=eng_headers)
    assert res.status_code == 200, f"Submit failed: {res.text}"
    print("10. Exam submitted.")
    
    # 10. Check Engineer Dashboard
    res = eng_session.get(f"{BASE_URL}/api/assessment/my-dashboard", headers=eng_headers)
    assert res.status_code == 200, f"Eng dashboard failed: {res.text}"
    radar = res.json()['skills_radar']
    assert len(radar) > 0 and radar[0]['score'] == 10.0, "Score not reflecting in dashboard"
    print("11. Engineer dashboard reflects auto-graded score correctly.")
    
    # 11. Check Leader Dashboard
    res = session.get(f"{BASE_URL}/api/admin/dashboard", headers=headers)
    assert res.status_code == 200, f"Leader dashboard failed: {res.text}"
    dashboard = res.json()['dashboard']
    eng_data = next((d for d in dashboard if d['user']['id'] == eng_id), None)
    assert eng_data is not None and len(eng_data['skills_radar']) > 0 and eng_data['skills_radar'][0]['score'] == 10.0, "Leader dashboard not reflecting score"
    print("12. Leader dashboard reflects score correctly.")
    
    print("--- ALL TESTS PASSED SUCCESSFULLY! ---")

if __name__ == '__main__':
    test_full_flow()
