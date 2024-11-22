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
    current_lecture = cursor.fetchone()
    classroom = session.get('classroom', '未登録')
    seat_number = session.get('seat_number', '未登録')
    period = session.get('period', '未登録')
    return render_template(
        'student/main.html', 
        classroom=classroom, 
        seat_number=seat_number, 
        period=period,
        current_lecture=current_lecture
    )


@main_bp.route('/exit', methods=['POST'])
@student_required
def exit_lecture():
    conn = current_app.get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT sp.id
        FROM student_participations sp
        JOIN subject_counts sc ON sp.subject_count_id = sc.id
        WHERE sp.student_subject_id IN (
            SELECT id FROM student_subjects WHERE student_id = ?
        )
        AND sc.lecture_active = 1
        AND sp.exit_time IS NULL
    ''', (current_user.id,))
    active_participations = cursor.fetchall()


    if not active_participations:
        flash("現在参加中の講義がありません。","error")

    elif len(active_participations) > 1:
        flash("複数の講義が未退出状態です。管理者に連絡してください。","error")

        # # 追加処理: 教員に通知
        # cursor.execute('''
        #     SELECT ss.subject_id, sp.seat_number
        #     FROM student_participations sp
        #     JOIN student_subjects ss ON sp.student_subject_id = ss.id
        #     WHERE sp.id = ?
        # ''', (participation['id'],))
        # subject_info = cursor.fetchone()

        # if subject_info:
        #     subject_id = subject_info['subject_id']
        #     seat_number = subject_info['seat_number']

        #     # WebSocketを利用して通知を送信（例: Socket.IO）
        #     from app import socketio
        #     socketio.emit('student_exit', {
        #         'student_id': current_user.id,
        #         'subject_id': subject_id,
        #         'seat_number': seat_number
        #     }, broadcast=True)

        # セッションにアラートメッセージを設定
        # 講義から退出する
    else:
        # 講義から退出する
        participation_id = active_participations[0][0]  # IDだけ取得
        cursor.execute('''
            UPDATE student_participations
            SET exit_time = ?
            WHERE id = ?
        ''', (datetime.now(), participation_id))
        conn.commit()

        flash("講義から退出しました", "success")
    return redirect(url_for('app.student.dashboard.dashboard'))
