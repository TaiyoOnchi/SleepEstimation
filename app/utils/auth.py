from flask import session,current_app
from flask_login import current_user
from app.models.student import Student
from app.models.teacher import Teacher



def load_user(user_id):
    conn = current_app.get_db()
    cursor = conn.cursor()

    role = session.get('role')
    user_data = None

    try:
        if role == 'student':
            cursor.execute('SELECT id, student_number, password, last_name, first_name, gender, in_lecture, right_eye_baseline, left_eye_baseline FROM students WHERE id = ?', (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                return Student(*user_data)

        elif role == 'teacher':
            cursor.execute('SELECT id, teacher_number, password, last_name, first_name FROM teachers WHERE id = ?', (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                return Teacher(*user_data)
    finally:
        pass
    
    return None


