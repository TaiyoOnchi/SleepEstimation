from flask import Blueprint, render_template, session, redirect, url_for, request,current_app,flash
from flask_login import login_required, current_user
from app.utils import student_required
from datetime import datetime
from app import socketio


lecture_bp = Blueprint('lecture', __name__)


@lecture_bp.route('/lecture', methods=['GET', 'POST'])
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


@lecture_bp.route('/lecture/register', methods=['GET', 'POST'])
@student_required
def register():
    conn = current_app.get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        subject_name = request.form.get('subject_name')
        cursor.execute('SELECT id FROM subjects WHERE subject_name = ?', (subject_name,))
        subject = cursor.fetchone()

        if not subject:
            flash("講義が見つかりません。", "error")
            return redirect(url_for('app.student.lecture.register'))

        # 履修登録
        cursor.execute('''
            INSERT INTO student_subjects (student_id, subject_id)
            SELECT ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM student_subjects WHERE student_id = ? AND subject_id = ?
            )
        ''', (current_user.id, subject['id'], current_user.id, subject['id']))
        conn.commit()

        flash("講義を履修登録しました。", "success")
        return redirect(url_for('app.student.dashboard.dashboard'))

    # 講義リストを取得
    cursor.execute('SELECT subject_name FROM subjects')
    subjects = cursor.fetchall()

    return render_template('student/lecture/register.html', subjects=subjects)


@lecture_bp.route('/lecture/join', methods=['GET', 'POST'])
@student_required
def join():
    conn = current_app.get_db()
    cursor = conn.cursor()

    # 学生が他のアクティブな講義に参加中か確認
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
    active_participation = cursor.fetchone()
    
    

    if active_participation:
        return redirect(url_for('app.student.main.main', 
                                alert_message="すでに講義に参加済みです", 
                                alert_type="error"))

    # 学生が履修している講義かつ開講中の講義を取得
    cursor.execute('''
        SELECT subjects.id AS subject_id, subjects.subject_name, subject_counts.id AS session_id,
               subject_counts.classroom, subject_counts.day_of_week, subject_counts.period, subject_counts.start_time
        FROM student_subjects
        JOIN subjects ON student_subjects.subject_id = subjects.id
        JOIN subject_counts ON subjects.id = subject_counts.subject_id
        WHERE student_subjects.student_id = ? AND subject_counts.lecture_active = 1
    ''', (current_user.id,))
    active_lectures = cursor.fetchall()

    # 開講中の講義がない場合はダッシュボードにリダイレクト
    if not active_lectures:
        return render_template('student/dashboard.html', alert_message="現在、開講中の講義はありません。(※開講中の講義に出席するには、履修登録から講義を選択してください)", alert_type="warning")

    if request.method == 'POST':
        # 学生が参加コードで講義に参加する処理
        join_code = request.form.get('join_code')
        session_id = request.form.get('session_id')
        # session_id が選択されているか確認
        if not session_id:
            flash("講義を選択してください。", "error")
            return redirect(url_for('app.student.lecture.join'))

        # 参加コードが4桁の数字であるか確認
        if not (join_code.isdigit() and len(join_code) == 4):
            flash("参加コードは4桁の数字で入力してください。", "error")
            return redirect(url_for('app.student.lecture.join'))

        # 選択した講義の session_id と参加コードが一致するか確認
        cursor.execute('''
            SELECT id
            FROM subject_counts
            WHERE id = ? AND join_code = ? AND lecture_active = 1
        ''', (session_id, join_code))
        session_result = cursor.fetchone()

        if session_result:
            # 学生を講義に参加させるロジック
            # 既存の参加記録を確認
            cursor.execute('''
                SELECT id
                FROM student_participations
                WHERE student_subject_id = (
                    SELECT id FROM student_subjects WHERE student_id = ? AND subject_id = (
                        SELECT subject_id FROM subject_counts WHERE id = ?
                    )
                )
                AND subject_count_id = ?
            ''', (current_user.id, session_id, session_id))
            existing_participation = cursor.fetchone()

            if existing_participation:
                # 既に参加している場合
                return redirect(url_for('app.student.lecture.join', 
                                alert_message="この講義はすでに退出済みです", 
                                alert_type="error"))
            else:
                # 新しい参加記録を作成
                cursor.execute('''
                    INSERT INTO student_participations (student_subject_id, subject_count_id, attendance_time)
                    SELECT student_subjects.id, ? AS subject_count_id, datetime('now')
                    FROM student_subjects
                    WHERE student_subjects.student_id = ? AND student_subjects.subject_id = (
                        SELECT subject_id FROM subject_counts WHERE id = ?
                    )
                ''', (session_id, current_user.id, session_id))
                conn.commit()
                
                    # 参加した学生の詳細を取得
                cursor.execute("""
                    SELECT students.student_number, students.last_name, students.first_name,
                        students.kana_last_name, students.kana_first_name,
                        student_participations.attendance_time, student_participations.exit_time,
                        student_participations.attention_count, student_participations.warning_count
                    FROM student_participations
                    JOIN student_subjects ON student_participations.student_subject_id = student_subjects.id
                    JOIN students ON student_subjects.student_id = students.id
                    WHERE student_participations.subject_count_id = ? AND student_subjects.student_id = ?
                """, (session_id, current_user.id))
                student_data = cursor.fetchone()

                # 講義に紐づく教員のIDを取得
                cursor.execute('''
                    SELECT teachers.id
                    FROM teachers
                    JOIN subjects ON teachers.id = subjects.teacher_id
                    JOIN subject_counts ON subjects.id = subject_counts.subject_id
                    WHERE subject_counts.id = ?
                ''', (session_id,))
                teacher_data = cursor.fetchone()

                if not teacher_data:
                    flash("教員情報が見つかりません。", "error")
                    return redirect(url_for('app.student.lecture.join'))

                teacher_id = teacher_data[0]
                socketio.emit('student_joined', {
                    'student_number': student_data[0],
                    'last_name': student_data[1],
                    'first_name': student_data[2],
                    'kana_last_name': student_data[3],
                    'kana_first_name': student_data[4],
                    'attendance_time': student_data[5],
                    'exit_time': student_data[6],
                    'attention_count': student_data[7],
                    'warning_count': student_data[8],
                }, room=f"teacher_{teacher_id}")  # ルーム名を動的に生成




                return redirect(url_for('app.student.main.main', 
                                alert_message="講義に参加しました", 
                                alert_type="error"))
        else:
            flash("無効な参加コードです。", "error")

    return render_template('student/lecture/join.html', active_lectures=active_lectures)


@lecture_bp.route('/lecture/exit', methods=['POST'])
@student_required
def exit():
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
