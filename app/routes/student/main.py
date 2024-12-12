from flask import Blueprint, render_template, session,current_app
from flask_login import current_user
from app import socketio
from app.utils import student_required




main_bp = Blueprint('main', __name__)

@main_bp.route('/main')
@student_required
def main():
    conn = current_app.get_db()
    cursor = conn.cursor()

    # 学生が参加中の講義情報を取得
    cursor.execute('''
        SELECT sp.id, sc.classroom, sc.day_of_week, sc.period, sc.start_time, sc.subject_id, sp.seat_number
        FROM student_participations sp
        JOIN subject_counts sc ON sp.subject_count_id = sc.id
        WHERE sp.student_subject_id IN (
            SELECT id FROM student_subjects WHERE student_id = ?
        )
        AND sc.end_time IS NULL
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
        subject_id = lecture_info[5]  # subject_id を取得
        seat_number = lecture_info[6]  # 座席番号を取得
    else:
        student_participation_id = None
        current_lecture = {}
        subject_id = None  # デフォルト値またはエラーハンドリング
        seat_number = None  # 座席番号のデフォルト値

    # student_subjects の情報を取得
    cursor.execute('''
        SELECT total_attentions, total_warnings
        FROM student_subjects
        WHERE student_id = ? AND subject_id = ?
    ''', (current_user.id, subject_id))
    subject_stats = cursor.fetchone()

    total_attentions = subject_stats[0]
    total_warnings = subject_stats[1]

    # student_participations の情報を取得
    cursor.execute('''
        SELECT attention_count, warning_count
        FROM student_participations
        WHERE id = ?
    ''', (student_participation_id,))
    participation_stats = cursor.fetchone()

    attention_count = participation_stats[0] if participation_stats else 0
    warning_count = participation_stats[1] if participation_stats else 0


    return render_template('student/main.html',
        student_participation_id=student_participation_id,
        current_lecture=current_lecture,
        total_attentions=total_attentions,
        total_warnings=total_warnings,
        attention_count=attention_count,
        warning_count=warning_count,
        seat_number=seat_number  # 座席番号をテンプレートに渡す
    )
