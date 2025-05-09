from flask import Blueprint, render_template, redirect,current_app,flash,url_for,request,jsonify
from flask_login import current_user
from app.utils import teacher_required
from datetime import datetime, timedelta
import random
import string
from app import socketio


lecture_bp = Blueprint('lecture', __name__)

@lecture_bp.route('/<int:subject_id>')
@teacher_required
def show(subject_id):
    conn = current_app.get_db()
    cursor = conn.cursor()
    
    # 講義の詳細を取得
    cursor.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,))
    subject = cursor.fetchone()
    
    # 講義回情報を取得
    cursor.execute("SELECT * FROM subject_counts WHERE subject_id = ?", (subject_id,))
    lecture_sessions = cursor.fetchall()
    
    # 各セッションの開始時刻と終了時刻をdatetimeオブジェクトに変換
    for i, session in enumerate(lecture_sessions):
        # Rowオブジェクトを辞書に変換
        session_dict = dict(session)  # Rowを辞書に変換
        
        # 日時の変換処理
        if session_dict.get('start_time'):
            start_time = datetime.strptime(session_dict['start_time'], '%Y-%m-%d %H:%M:%S.%f')
            # 年月日時分の形式に変換（秒を省略）
            session_dict['start_time'] = start_time.strftime('%Y-%m-%d %H:%M')  # 年-月-日 時:分
        if session_dict.get('end_time'):
            end_time = datetime.strptime(session_dict['end_time'], '%Y-%m-%d %H:%M:%S.%f')
            # 年月日時分の形式に変換（秒を省略）
            session_dict['end_time'] = end_time.strftime('%Y-%m-%d %H:%M')  # 年-月-日 時:分
        
        # 辞書を新しい形式に更新
        lecture_sessions[i] = session_dict
        
    # 現在アクティブな講義（開講中の講義）を取得
    cursor.execute("""
        SELECT sc.*, s.subject_name
        FROM subject_counts sc
        JOIN subjects s ON sc.subject_id = s.id
        WHERE sc.end_time IS NULL AND s.teacher_id = ?
    """, (current_user.id,))
    another_active_session = cursor.fetchone()



    return render_template('teacher/lecture/show.html', subject=subject, lecture_sessions=lecture_sessions, another_active_session=another_active_session)


# 講義コード生成
def generate_join_code():
    return ''.join(random.choices(string.digits, k=4))

@lecture_bp.route('/start/<int:subject_id>', methods=['GET', 'POST'])
@teacher_required
def start_session(subject_id):
    conn = current_app.get_db()
    cursor = conn.cursor()

    # 既にアクティブな講義が存在するか確認
    cursor.execute('SELECT subject_id FROM subject_counts WHERE end_time IS NULL AND subject_id IN (SELECT id FROM subjects WHERE teacher_id = ?)', (current_user.id,))
    active_lecture = cursor.fetchone()
    if active_lecture:
        flash("アクティブな講義が既に存在しています。終了してください。","error")
        return redirect(url_for('app.teacher.lecture.show', subject_id=active_lecture['subject_id']))

    # subjectsテーブルからデフォルトの曜日、時限、教室を取得
    cursor.execute('''
        SELECT default_day_of_week, default_period, default_classroom 
        FROM subjects 
        WHERE id = ?
    ''', (subject_id,))
    subject_defaults = cursor.fetchone()

    if not subject_defaults:
        return "指定された講義が見つかりません。", 404

    default_day_of_week, default_period, default_classroom = subject_defaults

    if request.method == 'POST':
        new_day_of_week = request.form.get('day_of_week', default_day_of_week)
        new_period = request.form.get('period', default_period)
        new_classroom = request.form.get('classroom', default_classroom)
        
        # 現在時刻を取得
        start_time = datetime.now()
        
        join_code = generate_join_code()

        # 新しい講義回データを追加
        cursor.execute('''
            INSERT INTO subject_counts (subject_id, classroom, day_of_week, period, start_time, join_code)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (subject_id, new_classroom, new_day_of_week, new_period, start_time, join_code))
        conn.commit()
        
        # 挿入した行のIDを取得
        session_id = cursor.lastrowid
        

        flash('講義を開始しました', "success")
        return redirect(url_for('app.teacher.lecture.session', session_id=session_id, subject_id=subject_id))

    return render_template(
        'teacher/lecture/start.html',
        subject_id=subject_id,
        default_day_of_week=default_day_of_week,
        default_period=default_period,
        default_classroom=default_classroom
    )
    
    










# 講義終了の処理
@lecture_bp.route('/end/<int:session_id>', methods=['POST'])
@teacher_required
def end_session(session_id):
    conn = current_app.get_db()
    cursor = conn.cursor()

    # 現在時刻を取得
    end_time = datetime.now()

    # アクティブな講義を終了する
    cursor.execute(
        """
        UPDATE subject_counts 
        SET end_time = ? 
        WHERE id = ? AND end_time IS NULL
        """,
        (end_time, session_id,)
    )
    
    # 参加している学生の学籍番号とparticipation_idを取得
    cursor.execute(
        """
        SELECT s.student_number, sp.id AS participation_id
        FROM students s
        JOIN student_subjects ss ON s.id = ss.student_id
        JOIN student_participations sp ON ss.id = sp.student_subject_id
        WHERE sp.subject_count_id = ? AND sp.exit_time IS NULL
        """,
        (session_id,)
    )
    students = cursor.fetchall()
    
    
    # student_participationsのexit_timeを更新
    cursor.execute(
        """
        UPDATE student_participations 
        SET exit_time = ? 
        WHERE subject_count_id = ? AND exit_time IS NULL
        """,
        (end_time, session_id,)
    )

    conn.commit()

    # 終了した講義のsubject_idを取得する
    cursor.execute(
        "SELECT subject_id FROM subject_counts WHERE id = ?", (session_id,)
    )
    subject = cursor.fetchone()
    subject_id = subject['subject_id'] if subject else None
    
        # 学生に講義終了を通知
    for student in students:
        student_number = student['student_number']
        participation_id = student['participation_id']
        socketio.emit('session_exit', {
            'message': '講義が終了したため、退出します。', 
            'redirect_url': url_for('app.student.lecture.show', participation_id=participation_id)
        }, room=student_number)

    if subject_id:
        flash("講義を終了しました。", "success")
        return redirect(url_for('app.teacher.lecture.show', subject_id=subject_id))
    else:
        flash("講義が見つかりませんでした。", "error")
        return redirect(url_for('app.teacher.dashboard.dashboard'))






@lecture_bp.route('/create', methods=['POST'])
@teacher_required
def create():
    conn = current_app.get_db()
    cursor = conn.cursor()

    # # 既にアクティブな講義が存在するか確認
    # cursor.execute('SELECT subject_id FROM subject_counts WHERE lecture_active = 1 AND subject_id IN (SELECT id FROM subjects WHERE teacher_id = ?)', (current_user.id,))
    # active_lecture = cursor.fetchone()
    # if active_lecture:
    #     flash("アクティブな講義が既に存在しています。終了してください。")
    #     return redirect(url_for('app.teacher.lecture.show', subject_id=active_lecture['subject_id']))

    # 入力された講義情報の取得
    subject_name = request.form.get('subject_name')
    default_classroom = request.form.get('default_classroom')
    default_day_of_week = request.form.get('default_day_of_week')
    default_period = int(request.form.get('default_period'))
    eor_threshold = int(request.form.get('eor_threshold') or 50)  # デフォルトを50に設定

    # 重複する講義名と曜日、教室、時限の確認
    cursor.execute('SELECT COUNT(*) FROM subjects WHERE subject_name = ?', (subject_name,))
    if cursor.fetchone()[0] > 0:
        flash("同じ講義名が既に存在します。異なる名前を使用してください。", "error")
        return redirect(url_for('app.teacher.lecture.new'))

    cursor.execute('''
        SELECT COUNT(*) FROM subjects 
        WHERE default_classroom = ? AND default_day_of_week = ? AND default_period = ?
    ''', (default_classroom, default_day_of_week, default_period))
    if cursor.fetchone()[0] > 0:
        flash("指定された教室、曜日、時限の講義が既に存在します。", "error")
        return redirect(url_for('app.teacher.lecture.new'))

    # 新しい講義を登録
    cursor.execute('''
        INSERT INTO subjects (teacher_id, subject_name, default_classroom, default_day_of_week, 
                              default_period, eor_threshold)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, subject_name, default_classroom, default_day_of_week, default_period, eor_threshold))
    conn.commit()

    flash("講義が正常に作成されました。", "success")
    return redirect(url_for('app.teacher.dashboard.dashboard'))



@lecture_bp.route('/new')
@teacher_required
def new():
    # GETリクエストの場合、フォームを表示
    return render_template('teacher/lecture/new.html')









@lecture_bp.route('/session/<int:session_id>')
@teacher_required
def session(session_id):
    conn = current_app.get_db()
    cursor = conn.cursor()

    # session_idに基づいて講義回の詳細を取得
    cursor.execute("SELECT * FROM subject_counts WHERE id = ?", (session_id,))
    lecture_session = cursor.fetchone()
    
    # 日時のフォーマットを追加
    if lecture_session:
        lecture_session = {
            **lecture_session,
            'start_time': datetime.strptime(lecture_session['start_time'][:16], '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M') if lecture_session['start_time'] else None,
            'end_time': datetime.strptime(lecture_session['end_time'][:16], '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M') if lecture_session['end_time'] else None,
        }
        
        # 第何回かを計算
        subject_id = lecture_session['subject_id']
        cursor.execute("""
            SELECT id
            FROM subject_counts
            WHERE subject_id = ?
            ORDER BY id
        """, (subject_id,))
        all_sessions = cursor.fetchall()
        session_number = next((i + 1 for i, session in enumerate(all_sessions) if session['id'] == session_id), None)
        lecture_session['session_number'] = session_number
        
        # lecture_sessionのsubject_count_idに基づいてsubject_nameを取得
        subject_id = lecture_session['subject_id']
        cursor.execute("SELECT subject_name FROM subjects WHERE id = ?", (subject_id,))
        subject_name = cursor.fetchone()

        # subject_nameが取得できた場合、lecture_sessionに追加
        if subject_name:
            lecture_session['subject_name'] = subject_name['subject_name']

    # 講義回に参加している学生の詳細を取得
    cursor.execute("""
        SELECT students.id, students.student_number, students.last_name, students.first_name, students.kana_last_name,students.kana_first_name,student_participations.attendance_time, student_participations.attention_count, student_participations.warning_count, student_participations.seat_number
        FROM student_participations
        JOIN student_subjects ON student_participations.student_subject_id = student_subjects.id
        JOIN students ON student_subjects.student_id = students.id
        WHERE student_participations.subject_count_id = ?
    """, (session_id,))
    student_participations = cursor.fetchall()
    student_participations=format_times(student_participations,'attendance_time')
    

    
    # 現在時刻の30秒前を取得
    one_minute_ago = datetime.now() - timedelta(minutes=0.5)

    # 開眼率が30秒間記録されていない学生を取得
    cursor.execute('''
        SELECT students.id, students.student_number, students.last_name, students.first_name, students.kana_last_name,students.kana_first_name,student_participations.attendance_time, student_participations.attention_count, student_participations.warning_count,student_participations.seat_number
        FROM student_participations 
        JOIN student_subjects ON student_participations.student_subject_id = student_subjects.id
        JOIN students ON student_subjects.student_id = students.id
        WHERE student_participations.subject_count_id = ?
        AND student_participations.id NOT IN (
            SELECT student_participation_id
            FROM eye_openness
            WHERE timestamp >= ?
        ) AND student_participations.attendance_time <= ? AND student_participations.exit_time IS NULL
    ''', (session_id, one_minute_ago, datetime.now()))

    inactive_students = cursor.fetchall()
    inactive_students=format_times(inactive_students,'attendance_time')
    

    return render_template('teacher/lecture/session.html', 
                           lecture_session=lecture_session,
                           student_participations=student_participations,
                           inactive_students=inactive_students
                           )
    
    
@lecture_bp.route('/lecture/check_eye_openness', methods=['GET'])
@teacher_required
def check_eye_openness():
    session_id = request.args.get('session_id')  # フロントから渡されるセッションID
    if not session_id:
        return jsonify({'error': 'Missing session_id'}), 400

    conn = current_app.get_db()
    cursor = conn.cursor()

    # 現在時刻の30秒前を取得
    one_minute_ago = datetime.now() - timedelta(minutes=0.5)

    # 開眼率が30秒間記録されていない学生を取得
    cursor.execute('''
        SELECT students.id, students.student_number, students.last_name, students.first_name, students.kana_last_name,students.kana_first_name,student_participations.attendance_time, student_participations.attention_count, student_participations.warning_count,student_participations.seat_number
        FROM student_participations 
        JOIN student_subjects ON student_participations.student_subject_id = student_subjects.id
        JOIN students ON student_subjects.student_id = students.id
        WHERE student_participations.subject_count_id = ?
        AND student_participations.id NOT IN (
            SELECT student_participation_id
            FROM eye_openness
            WHERE timestamp >= ?
        ) AND student_participations.attendance_time <= ? AND student_participations.exit_time IS NULL
    ''', (session_id, one_minute_ago, datetime.now()))

    inactive_students = cursor.fetchall()
    inactive_students=format_times(inactive_students,'attendance_time')

    return jsonify({'inactive_students': inactive_students})




@lecture_bp.route('/create_warning')
@teacher_required
def create_warning():
    student_id = request.args.get('student_id')
    conn = current_app.get_db()
    cursor = conn.cursor()

    # 学生情報の取得
    cursor.execute('''
        SELECT *
        FROM students 
        WHERE students.id = ?
    ''', (student_id,))
    student_info = cursor.fetchone()
    
    if not student_info:
        flash("学生情報が見つかりません", "error")
        return redirect(url_for('app.teacher.dashboard.dashboard'))

    return render_template('teacher/lecture/warning.html', student_info=student_info)


@lecture_bp.route('/submit_warning', methods=['POST'])
@teacher_required
def submit_warning():
    student_id = request.form['student_id']
    student_number = request.form['student_number']
    reason = request.form['reason']
    timestamp = datetime.now()

    conn = current_app.get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT sp.id, sp.subject_count_id
        FROM student_participations sp
        JOIN student_subjects ss ON sp.student_subject_id = ss.id
        JOIN students ON ss.student_id = students.id
        WHERE ss.student_id = ?
        AND sp.exit_time IS NULL
    ''', (student_id,))
    result = cursor.fetchone()

    if not result:
        flash("学生の参加情報が見つかりませんでした。", "error")
        return redirect(url_for('teacher_dashboard'))

    # `fetchone()`はタプルを返すので、最初の値を取得
    participation_id = result[0]
    subject_counts_id = result[1]
    
    
    # 注意回数が記録された際の処理
    cursor.execute('''
        UPDATE student_subjects
        SET total_warnings = total_warnings + 1
        WHERE id = (
            SELECT ss.id 
            FROM student_subjects ss
            JOIN student_participations sp ON ss.id = sp.student_subject_id
            WHERE sp.id = ?
        )
    ''', (participation_id,))
    
    cursor.execute('''
        UPDATE student_participations
        SET warning_count = warning_count + 1
        WHERE id = ?
    ''', (participation_id,))
    
    # 警告テーブルに挿入
    cursor.execute('''
        INSERT INTO warnings (student_participation_id, timestamp, reason)
        VALUES (?, ?, ?)
    ''', (participation_id, timestamp, reason))
    
    conn.commit()
    print(f'学籍番号{student_number}')
    # 学生に警告を通知
    socketio.emit(
        'eye_openness_alert', 
        {'message': f'教員から警告が送信されました。\n理由：{reason}'}, 
        room=student_number
    )

    flash("警告が作成されました", "success")
    return redirect(url_for('app.teacher.lecture.session',session_id=subject_counts_id))



@lecture_bp.route('/session/<int:session_id>/student/<int:student_id>')
@teacher_required
def session_student_details(session_id, student_id):
    conn = current_app.get_db()
    cursor = conn.cursor()
    
    # `subjectsのeor_threshold` を取得
    cursor.execute('''
        SELECT subject_id
        FROM subject_counts
        WHERE subject_counts.id = ?
    ''', (session_id,))
    subject_id_row = cursor.fetchone()

    # subject_id_row がタプル形式の場合
    if subject_id_row:
        subject_id = subject_id_row[0]  # sqlite3.Row から subject_id を取得

        cursor.execute('''
            SELECT eor_threshold
            FROM subjects
            WHERE subjects.id = ?
        ''', (subject_id,))
        eor_threshold_row = cursor.fetchone()

        if eor_threshold_row:
            eor_threshold = eor_threshold_row[0]  # eor_threshold を取得
        else:
            raise ValueError("eor_threshold could not be found for the given subject_id")
    else:
        raise ValueError("subject_id could not be found for the given session_id")
    



    # `student_subject_id` を取得
    cursor.execute('''
        SELECT ss.id
        FROM student_subjects ss
        JOIN subject_counts sc ON sc.subject_id = ss.subject_id
        WHERE ss.student_id = ? AND sc.id = ?
    ''', (student_id, session_id))
    student_subject_id = cursor.fetchone()
    
    if not student_subject_id:
        return "該当するデータが見つかりません", 404
    
    student_subject_id = student_subject_id[0]

    # 学生基本情報を取得
    cursor.execute('''
        SELECT student_number, kana_last_name, kana_first_name, last_name, first_name, face_photo
        FROM students
        WHERE id = ?
    ''', (student_id,))
    student_info = cursor.fetchone()
    
    # 講義全体の注意・警告回数を取得
    cursor.execute('''
        SELECT total_attentions, total_warnings
        FROM student_subjects
        WHERE id = ?
    ''', (student_subject_id,))
    lecture_totals = cursor.fetchone()

    # 学生の出席情報を取得
    cursor.execute('''
        SELECT attendance_time, exit_time, attention_count, warning_count
        FROM student_participations
        WHERE student_subject_id = ? AND subject_count_id = ?
    ''', (student_subject_id, session_id))
    participation_info = cursor.fetchone()
    
    # 日時のフォーマットを追加
    if participation_info:
        participation_info = {
            **participation_info,
            'attendance_time': datetime.strptime(participation_info['attendance_time'][:16], '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M') if participation_info['attendance_time'] else None,
            'exit_time': datetime.strptime(participation_info['exit_time'][:16], '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M') if participation_info['exit_time'] else None,
        }




    # attentions情報を取得
    cursor.execute('''
        SELECT *
        FROM attentions
        WHERE student_participation_id = (
            SELECT id
            FROM student_participations
            WHERE student_subject_id = ? AND subject_count_id = ?
        )
    ''', (student_subject_id, session_id))
    attentions = cursor.fetchall()
    attentions= format_times(attentions,'timestamp')
    



    # warnings情報を取得
    cursor.execute('''
        SELECT id, timestamp, reason
        FROM warnings
        WHERE student_participation_id = (
            SELECT id
            FROM student_participations
            WHERE student_subject_id = ? AND subject_count_id = ?
        )
    ''', (student_subject_id, session_id))
    warnings = cursor.fetchall()
    warnings= format_times(warnings,'timestamp')
    

    # eye_openness情報を取得
    cursor.execute('''
        SELECT timestamp, right_eye_openness, left_eye_openness
        FROM eye_openness
        WHERE student_participation_id = (
            SELECT id
            FROM student_participations
            WHERE student_subject_id = ? AND subject_count_id = ?
        )
    ''', (student_subject_id, session_id))
    eye_openness = cursor.fetchall()
    eye_openness= format_times(eye_openness,'timestamp')
   

    return render_template('teacher/lecture/session_student_details.html',
                        student_info=student_info,
                        lecture_totals=lecture_totals,
                        participation_info=participation_info,
                        attentions=attentions,
                        warnings=warnings,
                        eye_openness=eye_openness,
                        session_id=session_id,
                        eor_threshold=eor_threshold)


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