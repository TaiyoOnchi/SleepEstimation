from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app.utils import get_db_connection

show_bp = Blueprint('show', __name__)

@show_bp.route('/<student_number>')
@login_required
def show(student_number):
    if current_user.role == 'student' and current_user.student_number != student_number:
        flash('他の学生の情報にはアクセスできません。')
        return redirect(url_for('student.dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(''' 
        SELECT student_number, last_name, first_name, kana_last_name, kana_first_name, 
               face_photo, gender, is_active, right_eye_baseline, left_eye_baseline 
        FROM students 
        WHERE student_number = ?
    ''', (student_number,))
    
    student = cursor.fetchone()
    conn.close()

    if student:
        student_data = {
            'student_number': student[0],
            'last_name': student[1],
            'first_name': student[2],
            'kana_last_name': student[3],
            'kana_first_name': student[4],
            'face_photo': student[5],
            'gender': student[6],
            'is_active': student[7],
            'right_eye_baseline': student[8],
            'left_eye_baseline': student[9]
        }
        return render_template('student/student_profile.html', student=student_data)
    else:
        return "学生が見つかりません", 404
