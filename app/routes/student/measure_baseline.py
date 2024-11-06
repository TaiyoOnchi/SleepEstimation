from flask import Blueprint, render_template, session, flash, redirect, url_for
from app.utils import handle_authenticated_user

measure_baseline_bp = Blueprint('measure_baseline', __name__)

@measure_baseline_bp.route('/measure_eye_baseline')
def measure_baseline():
    redirect_response = handle_authenticated_user()
    if redirect_response:
        return redirect_response

    if session.get('student_info'):
        return render_template('student/measure_eye_baseline.html')
    else:
        flash('学籍番号や氏名を入力してください。')
        return redirect(url_for('app.student.register.register'))
