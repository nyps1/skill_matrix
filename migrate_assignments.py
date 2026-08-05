import sqlite3

def migrate():
    conn = sqlite3.connect('C:\\Users\\User\\.gemini\\antigravity\\scratch\\engineer_skill_assessment\\skill_assessment.db')
    cursor = conn.cursor()
    
    # Create the new table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_assigned_assessments (
            user_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, skill_id),
            FOREIGN KEY(user_id) REFERENCES users (id),
            FOREIGN KEY(skill_id) REFERENCES skill_categories (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == '__main__':
    migrate()
