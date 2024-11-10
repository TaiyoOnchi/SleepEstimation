from flask import current_app
from datetime import datetime

def save_eye_openness(conn ,student_number, right_eye_openness, left_eye_openness):
    cursor = conn.cursor()
    
    # 現在時刻を取得
    time = datetime.now()
    
    cursor.execute('''
        INSERT INTO eye_openness (student_id, right_eye_openness, left_eye_openness,timestamp)
        SELECT id, ?, ?, ? FROM students WHERE student_number = ?
    ''', (right_eye_openness, left_eye_openness,time, student_number))
    cursor.execute('''
        DELETE FROM eye_openness 
        WHERE id NOT IN (
            SELECT id FROM eye_openness 
            WHERE student_id = (SELECT id FROM students WHERE student_number = ?)
            ORDER BY timestamp DESC LIMIT 3
        ) AND student_id = (SELECT id FROM students WHERE student_number = ?)
    ''', (student_number, student_number))
    conn.commit()
    conn.close()
