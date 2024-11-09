from flask import Blueprint, render_template, session
from flask_login import login_required, current_user
from app import socketio
from app.utils import student_required


main_bp = Blueprint('main', __name__)

@main_bp.route('/main')
@login_required
@student_required
def main():
    classroom = session.get('classroom', '未登録')
    seat_number = session.get('seat_number', '未登録')
    period = session.get('period', '未登録')
    return render_template('student/main.html', classroom=classroom, seat_number=seat_number, period=period)
