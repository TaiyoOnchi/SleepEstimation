from flask import Blueprint, render_template, request, redirect, url_for, flash, session,current_app
from flask_login import login_user
from werkzeug.security import check_password_hash
from app.models import Student


login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'student_info' in session:
        session.pop('student_info', None)
    
    if request.method == 'POST':
        student_number = request.form['student_number']
        password = request.form['password']

        conn = current_app.get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, student_number, password, last_name, first_name, gender, in_lecture, right_eye_baseline, left_eye_baseline FROM students WHERE student_number = ?', (student_number,))
        user_data = cursor.fetchone()
        

        if user_data:
            student_id, student_number, hashed_password, last_name, first_name, gender, in_lecture, right_eye_baseline, left_eye_baseline = user_data
            if check_password_hash(hashed_password, password):
                student = Student(student_id, student_number, hashed_password, last_name, first_name, gender, in_lecture, right_eye_baseline, left_eye_baseline)
                login_user(student)
                session['role'] = 'student'
                
                return redirect(url_for('app.student.dashboard.dashboard'))
            else:
              flash("学籍番号かパスワードが違います。再度ログインしてください")
              return redirect(url_for('app.student.login.login'))
        else:
            flash("学籍番号かパスワードが違います。再度ログインしてください")
            return redirect(url_for('app.student.login.login'))
    return render_template('student/login.html')

