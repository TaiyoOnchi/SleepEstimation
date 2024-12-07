from flask import current_app
from datetime import datetime

def save_eye_openness(conn ,participation_id, right_eye_openness, left_eye_openness):
    cursor = conn.cursor()
    
    # 現在時刻を取得
    time = datetime.now()
    
    cursor.execute('''
        INSERT INTO eye_openness (student_participation_id, right_eye_openness, left_eye_openness,timestamp)
        SELECT id, ?, ?, ? FROM student_participations WHERE id = ?
    ''', (right_eye_openness, left_eye_openness, time, participation_id))
    conn.commit()
