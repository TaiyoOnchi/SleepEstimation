import sqlite3
import cv2 as cv
import base64
from werkzeug.security import generate_password_hash
from app.utils.database import get_db_connection

def save_baseline_to_database(best_frame, eye_openness, student_info):
    conn = get_db_connection()
    cursor = conn.cursor()

    _, buffer = cv.imencode('.jpg', best_frame)
    face_photo = base64.b64encode(buffer).decode('utf-8')

    cursor.execute('''
        INSERT INTO students (student_number, password, last_name, first_name, kana_last_name, kana_first_name, gender, right_eye_baseline, left_eye_baseline, face_photo, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        student_info['student_number'],
        student_info['password'],
        student_info['last_name'],
        student_info['first_name'],
        student_info['kana_last_name'],
        student_info['kana_first_name'],
        student_info['gender'],
        eye_openness['eye_right'],
        eye_openness['eye_left'],
        face_photo,
        1
    ))
    conn.commit()
    conn.close()
