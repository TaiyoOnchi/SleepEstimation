import sqlite3
from app.utils.database import get_db_connection

def save_eye_openness(student_number, right_eye_openness, left_eye_openness):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO eye_openness (student_id, right_eye_openness, left_eye_openness)
        SELECT id, ?, ? FROM students WHERE student_number = ?
    ''', (right_eye_openness, left_eye_openness, student_number))
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
