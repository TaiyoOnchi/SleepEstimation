from flask import Blueprint, render_template, redirect,current_app,session,flash,url_for,request
from flask_login import login_required, current_user
from app.utils import teacher_required
from datetime import datetime
import random
import string


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


    return render_template('teacher/lecture/show.html', subject=subject, lecture_sessions=lecture_sessions)


# 講義コード生成
def generate_join_code():
    return ''.join(random.choices(string.digits, k=4))

@lecture_bp.route('/start/<int:subject_id>', methods=['GET', 'POST'])
@teacher_required
def start_session(subject_id):
    conn = current_app.get_db()
    cursor = conn.cursor()

    # 既にアクティブな講義が存在するか確認
    cursor.execute('SELECT subject_id FROM subject_counts WHERE lecture_active = 1 AND subject_id IN (SELECT id FROM subjects WHERE teacher_id = ?)', (current_user.id,))
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
            INSERT INTO subject_counts (subject_id, classroom, day_of_week, period, start_time, lecture_active, join_code)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (subject_id, new_classroom, new_day_of_week, new_period, start_time,True, join_code))
        conn.commit()

        flash('講義を開始しました', "success")
        return redirect(url_for('app.teacher.lecture.show', subject_id=subject_id))

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
    cursor.execute("UPDATE subject_counts SET lecture_active = 0, end_time = ? WHERE id = ? AND lecture_active = 1", (end_time, session_id,))
    conn.commit()
    
    # 終了した講義のsubject_idを取得する
    cursor.execute("SELECT subject_id FROM subject_counts WHERE id = ?", (session_id,))
    subject = cursor.fetchone()
    subject_id = subject['subject_id'] if subject else None
    
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
    ero_threshold = int(request.form.get('ero_threshold') or 50)  # デフォルトを50に設定

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
                              default_period, ero_threshold)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, subject_name, default_classroom, default_day_of_week, default_period, ero_threshold))
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
    cursor.execute("""
        SELECT * FROM subject_counts WHERE id = ?
    """, (session_id,))
    lecture_session = cursor.fetchone()

    # 講義回に参加している学生の詳細を取得
    cursor.execute("""
        SELECT students.id, students.last_name, students.first_name, student_participations.attendance_time,
               student_participations.exit_time, student_participations.attention_count, student_participations.warning_count
        FROM student_participations
        JOIN student_subjects ON student_participations.student_subject_id = student_subjects.id
        JOIN students ON student_subjects.student_id = students.id
        WHERE student_participations.subject_count_id = ?
    """, (session_id,))
    student_participations = cursor.fetchall()

    return render_template('teacher/lecture/session.html', 
                           lecture_session=lecture_session, 
                           student_participations=student_participations)
