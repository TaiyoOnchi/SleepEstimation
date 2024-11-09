from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_login import login_required, current_user
from app.utils import student_required


lecture_bp = Blueprint('lecture', __name__)

@lecture_bp.route('/lecture', methods=['GET', 'POST'])
@login_required
@student_required
def lecture():
    #print(f"Current user role: {current_user.role}", flush=True)


    if 'student_info' in session:
        session.pop('student_info', None)

    if request.method == 'POST':
        classroom = request.form.get('classroom')
        seat_number = request.form.get('seat_number')
        period = request.form.get('period')

        session['classroom'] = classroom
        session['seat_number'] = seat_number
        session['period'] = period

        return redirect(url_for('app.student.main.main'))

    return render_template('student/lecture.html')
