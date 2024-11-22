from flask import Blueprint, render_template, session, flash, redirect, url_for,current_app
from app.utils import handle_authenticated_user, generate_token 

measure_baseline_bp = Blueprint('measure_baseline', __name__)

@measure_baseline_bp.route('/measure_eye_baseline')
def measure_baseline():
    redirect_response = handle_authenticated_user()
    if redirect_response:
        return redirect_response

    student_info = session.get('student_info')
    if not student_info:
        flash('学籍番号や氏名を入力してください。',"error")
        return redirect(url_for('app.student.register.register'))

    student_number = student_info.get('student_number')

    # データベース接続と重複確認
    conn = current_app.get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE student_number = ?', (student_number,))
    existing_user = cursor.fetchone()

    if existing_user:
        flash('既に登録されている学籍番号です。ログインしてください。',"error")
        return redirect(url_for('app.student.login.login'))

    token = generate_token({'student_info': student_info})
    return render_template('student/measure_eye_baseline.html', token=token)
