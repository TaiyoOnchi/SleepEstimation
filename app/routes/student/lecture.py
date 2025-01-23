from flask import Blueprint, render_template, session, redirect, url_for, request,current_app,flash
from flask_login import login_required, current_user
from app.utils import student_required
from datetime import datetime
from app import socketio


lecture_bp = Blueprint('lecture', __name__)





@lecture_bp.route('/lecture/register', methods=['GET', 'POST'])
@student_required
def register():
    conn = current_app.get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        subject_ids = request.form.getlist('subject_ids')
        for subject_id in subject_ids:
            cursor.execute('''
                INSERT INTO student_subjects (student_id, subject_id)
                SELECT ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM student_subjects WHERE student_id = ? AND subject_id = ?
                )
            ''', (current_user.id, subject_id, current_user.id, subject_id))
        conn.commit()

        flash("選択した講義を履修登録しました。", "success")
        return redirect(url_for('app.student.lecture.register'))

    # 履修済みの講義を取得
    cursor.execute('''
        SELECT 
            s.id,
            s.subject_name, 
            s.default_classroom, 
            s.default_day_of_week, 
            s.default_period,
            ss.total_attentions,
            ss.total_warnings,
            (SELECT COUNT(*) 
             FROM student_participations sp 
             JOIN subject_counts sc ON sp.subject_count_id = sc.id
             WHERE sp.student_subject_id = ss.id) AS attendance_count,
            (SELECT COUNT(*) 
             FROM subject_counts 
             WHERE subject_counts.subject_id = s.id) AS lecture_count
        FROM subjects s
        JOIN student_subjects ss ON s.id = ss.subject_id
        WHERE ss.student_id = ?
    ''', (current_user.id,))
    registered_subjects = cursor.fetchall()

    # ユーザーが履修していない講義を取得
    cursor.execute('''
        SELECT s.id, s.subject_name, s.default_classroom, s.default_day_of_week, s.default_period
        FROM subjects s
        WHERE NOT EXISTS (
            SELECT 1 FROM student_subjects ss
            WHERE ss.subject_id = s.id AND ss.student_id = ?
        )
    ''', (current_user.id,))
    subjects = cursor.fetchall()

    return render_template('student/lecture/register.html', 
                           registered_subjects=registered_subjects, 
                           subjects=subjects)





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
        AND sc.end_time IS NULL
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
        WHERE student_subjects.student_id = ? AND subject_counts.end_time IS NULL
    ''', (current_user.id,))
    active_lectures = cursor.fetchall()
    
    active_lectures = format_times(active_lectures, 'start_time')


    # 開講中の講義がない場合はダッシュボードにリダイレクト
    if not active_lectures:
        return render_template('student/dashboard.html', alert_message="現在、開講中の講義はありません。(※開講中の講義に出席するには、履修登録から講義を選択してください)", alert_type="warning")

    if request.method == 'POST':
        join_code = request.form.get('join_code')
        session_id = request.form.get('session_id')
        seat_number = request.form.get('seat_number')  # 座席番号を取得

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
            WHERE id = ? AND join_code = ? AND end_time IS NULL
        ''', (session_id, join_code))
        session_result = cursor.fetchone()

        if session_result:
            # 座席番号が他の学生と被らないか確認
            # --- 座席番号の重複チェック ---
            cursor.execute('''
                SELECT seat_number
                FROM student_participations
                WHERE subject_count_id = ? AND seat_number = ?
            ''', (session_id, seat_number))
            existing_seat = cursor.fetchone()

            if existing_seat:
                flash("選択した座席番号はすでに使用されています。別の番号を選択してください。", "error")
                return redirect(url_for('app.student.lecture.join'))
            # -------------------------

            attendance_time = datetime.now()
            # 新しい参加記録を作成
            cursor.execute('''
                INSERT INTO student_participations (student_subject_id, subject_count_id, attendance_time, seat_number)
                SELECT student_subjects.id, ? AS subject_count_id, ?, ? AS seat_number
                FROM student_subjects
                WHERE student_subjects.student_id = ? AND student_subjects.subject_id = (
                    SELECT subject_id FROM subject_counts WHERE id = ?
                )
            ''', (session_id, attendance_time,seat_number,current_user.id, session_id))
            conn.commit()

            # 参加した学生の詳細を取得
            cursor.execute("""
                SELECT students.id, students.student_number, students.last_name, students.first_name,
                    students.kana_last_name, students.kana_first_name,
                    strftime('%Y-%m-%d %H:%M', student_participations.attendance_time) AS attendance_time, 
                    student_participations.attention_count, student_participations.warning_count, student_participations.seat_number
                FROM student_participations
                JOIN student_subjects ON student_participations.student_subject_id = student_subjects.id
                JOIN students ON student_subjects.student_id = students.id
                WHERE student_participations.subject_count_id = ? AND student_subjects.student_id = ?
            """, (session_id, current_user.id))
            student_data = cursor.fetchone()



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
                'id': student_data[0],
                'student_number': student_data[1],
                'last_name': student_data[2],  
                'first_name': student_data[3], 
                'kana_last_name': student_data[4],
                'kana_first_name': student_data[5],
                'attendance_time': student_data[6],
                'attention_count': student_data[7],
                'warning_count': student_data[8],
                'seat_number': student_data[9],
            }, room=f"teacher_{teacher_id}")  # ルーム名を動的に生成

            return redirect(url_for('app.student.main.main', 
                                    alert_message="講義に参加しました", 
                                    alert_type="success"))
        else:
            flash("無効な参加コードです。", "error")

    return render_template('student/lecture/join.html', active_lectures=active_lectures)



@lecture_bp.route('/lecture/warnings/<int:participation_id>')
@student_required
def warnings(participation_id):
    conn = current_app.get_db()
    cursor = conn.cursor()

    # warnings テーブルからデータを取得
    cursor.execute('''
        SELECT id, timestamp, reason
        FROM warnings
        WHERE student_participation_id = ?
        ORDER BY timestamp DESC
    ''', (participation_id,))
    warnings_list = cursor.fetchall()

    return render_template('student/lecture/warnings.html', warnings=warnings_list)


@lecture_bp.route('/lecture/show/<int:participation_id>')
@student_required
def show(participation_id):
    conn = current_app.get_db()
    cursor = conn.cursor()

    # 学生が参加中の講義情報を取得
    cursor.execute('''
        SELECT sp.id, sc.classroom, sc.day_of_week, sc.period, sc.start_time, sc.end_time, sc.subject_id, sc.id AS subject_count_id, sp.seat_number
        FROM student_participations sp
        JOIN subject_counts sc ON sp.subject_count_id = sc.id
        WHERE sp.id = ?
    ''', (participation_id,))
    lecture_info = cursor.fetchone()

    if lecture_info:
        # 日時の変換処理（start_time をフォーマット）
        start_time = datetime.strptime(lecture_info[4], '%Y-%m-%d %H:%M:%S.%f')  # データベースのフォーマットに応じて調整
        formatted_start_time = start_time.strftime('%Y-%m-%d %H:%M')
        end_time = datetime.strptime(lecture_info[5], '%Y-%m-%d %H:%M:%S.%f')  # データベースのフォーマットに応じて調整
        formatted_end_time = end_time.strftime('%Y-%m-%d %H:%M')

        current_lecture = {
            "classroom": lecture_info[1],
            "day_of_week": lecture_info[2],
            "period": lecture_info[3],
            "start_time": formatted_start_time,  # フォーマット後の時刻を格納
            "end_time": formatted_end_time
        }
        subject_id = lecture_info[6]  # subject_id を取得
        subject_count_id = lecture_info[7]  # 現在の subject_count_id
        seat_number = lecture_info[8]  # 座席番号を取得
    else:
        return render_template('student/dashboard.html', alert_message="現在、参加中の講義はありません。", alert_type="warning")
    
    # subject_name の取得
    cursor.execute('''
        SELECT subject_name
        FROM subjects
        WHERE id = ?
    ''', (subject_id,))
    subject = cursor.fetchone()
    subject_name = subject[0] if subject else "不明"

    # 講義回数を取得
    cursor.execute('''
        SELECT id, start_time
        FROM subject_counts
        WHERE subject_id = ?
        ORDER BY start_time ASC
    ''', (subject_id,))
    all_lectures = cursor.fetchall()

    # 現在の講義が何回目かを計算
    lecture_number = 1
    for i, lecture in enumerate(all_lectures, start=1):
        if lecture[0] == subject_count_id:  # 現在の `subject_count_id` に一致する場合
            lecture_number = i
            break

    # student_subjects の情報を取得
    cursor.execute('''
        SELECT total_attentions, total_warnings
        FROM student_subjects
        WHERE student_id = ? AND subject_id = ?
    ''', (current_user.id, subject_id))
    subject_stats = cursor.fetchone()

    total_attentions = subject_stats[0] if subject_stats else 0
    total_warnings = subject_stats[1] if subject_stats else 0

    # student_participations の情報を取得
    cursor.execute('''
        SELECT attention_count, warning_count
        FROM student_participations
        WHERE id = ?
    ''', (participation_id,))
    participation_stats = cursor.fetchone()

    attention_count = participation_stats[0] if participation_stats else 0
    warning_count = participation_stats[1] if participation_stats else 0
    
    # attentions情報を取得
    cursor.execute('''
        SELECT *
        FROM attentions
        WHERE student_participation_id = ?
    ''', (participation_id,))
    attentions = cursor.fetchall()
    attentions= format_times(attentions,'timestamp')
    
    # warnings情報を取得
    cursor.execute('''
        SELECT id, timestamp, reason
        FROM warnings
        WHERE student_participation_id = ?
    ''', (participation_id,))
    warnings = cursor.fetchall()
    warnings= format_times(warnings,'timestamp')

    return render_template('student/lecture/show.html',
        student_participation_id=participation_id,
        current_lecture=current_lecture,
        total_attentions=total_attentions,
        total_warnings=total_warnings,
        attention_count=attention_count,
        warning_count=warning_count,
        seat_number=seat_number,  # 座席番号をテンプレートに渡す
        subject_name=subject_name,  # subject_name をテンプレートに渡す
        lecture_number=lecture_number,  # 講義回数をテンプレートに渡す
        attentions=attentions,
        warnings=warnings,
        subject_id=subject_id
    )


def format_times(data, key):
    """
    指定したキーの値をフォーマットする関数。
    :param data: 辞書のリストまたはsqlite3.Rowのリスト
    :param key: フォーマット対象のキー名
    :return: フォーマット済みの辞書リスト
    """
    formatted = []
    for item in data:
        # sqlite3.Rowを辞書に変換
        item_dict = dict(item)
        formatted.append({
            **item_dict,
            key: (
                datetime.strptime(str(item_dict[key])[:16], '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M') 
                if item_dict.get(key) 
                else None
            ),
        })
    return formatted


@lecture_bp.route('/lecture/subject_counts/<int:subject_id>')
@student_required
def subject_counts(subject_id):
    conn = current_app.get_db()
    cursor = conn.cursor()
    
    # subjectを取得
    cursor.execute('''
        SELECT *
        FROM subjects
        WHERE id = ?
    ''', (subject_id,))
    subject = cursor.fetchone()  # 1件だけ取得
    
    # データを辞書形式に変換
    if subject:
        subject = dict(zip([column[0] for column in cursor.description], subject))
    
    # 該当する subject_id のすべての subject_counts を取得
    cursor.execute('''
        SELECT id, start_time, end_time
        FROM subject_counts
        WHERE subject_id = ?
        ORDER BY start_time ASC
    ''', (subject_id,))
    lectures = cursor.fetchall()


    # タプルを辞書形式に変換
    lectures = [dict(zip([column[0] for column in cursor.description], row)) for row in lectures]

    # 時刻をフォーマット
    lectures = format_times(lectures, 'start_time')
    lectures = format_times(lectures, 'end_time')

    # student_participations を辞書形式で attention_count と warning_count を含むように修正
    cursor.execute('''
        SELECT sp.subject_count_id, sp.id, sp.attention_count, sp.warning_count
        FROM student_participations sp
        JOIN student_subjects ss ON sp.student_subject_id = ss.id
        WHERE ss.student_id = ? AND ss.subject_id = ?
    ''', (current_user.id, subject_id))
    participations = {row[0]: {'id': row[1], 'attention_count': row[2], 'warning_count': row[3]} for row in cursor.fetchall()}

    return render_template('student/lecture/subject_counts.html', subject=subject, lectures=lectures, participations=participations)
