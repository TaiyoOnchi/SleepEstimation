from flask import Blueprint, render_template, session,current_app,redirect,url_for,flash
from flask_login import login_required, current_user
from app import socketio
from app.utils import student_required
from datetime import datetime



main_bp = Blueprint('main', __name__)

@main_bp.route('/main')
@student_required
def main():
    conn = current_app.get_db()
    cursor = conn.cursor()
    # 学生が参加中の講義情報を取得
    cursor.execute('''
        SELECT sp.id, sc.classroom, sc.day_of_week, sc.period, sc.start_time
        FROM student_participations sp
        JOIN subject_counts sc ON sp.subject_count_id = sc.id
        WHERE sp.student_subject_id IN (
            SELECT id FROM student_subjects WHERE student_id = ?
        )
        AND sc.lecture_active = 1
        AND sp.exit_time IS NULL
    ''', (current_user.id,))
    lecture_info = cursor.fetchone()

    if lecture_info:
        student_participation_id = lecture_info[0]
        current_lecture = {
            "classroom": lecture_info[1],
            "day_of_week": lecture_info[2],
            "period": lecture_info[3],
            "start_time": lecture_info[4]
        }
    else:
        student_participation_id = None
        current_lecture = {}

    seat_number = session.get('seat_number', '未登録')

    return render_template('student/main.html',
        seat_number=seat_number,
        student_participation_id=student_participation_id,
        current_lecture=current_lecture
    )
