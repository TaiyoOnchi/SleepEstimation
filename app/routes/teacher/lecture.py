from flask import Blueprint, render_template, redirect,current_app,session,flash,url_for,request
from flask_login import login_required, current_user
from app.utils import teacher_required
from datetime import datetime
import sqlite3

lecture_bp = Blueprint('lecture', __name__)

@lecture_bp.route('/<int:subject_id>')
@teacher_required
def show(subject_id):
    conn = current_app.get_db()
    cursor = conn.cursor()
    
    # 講義の詳細を取得
    cursor.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,))
    subject = cursor.fetchone()
    
    # 参加学生の開眼率データを取得
    # SQL文の確認、エイリアスとカラム名を明確に
    # 指定されたsubject_idに紐づく講義回を取得
    cursor.execute("""
        SELECT * FROM subject_counts WHERE subject_id = ?
    """, (subject_id,))
    lecture_sessions = cursor.fetchall()
  
    return render_template('teacher/lecture/show.html', subject=subject, lecture_sessions=lecture_sessions)





@lecture_bp.route('/create', methods=['GET', 'POST'])
@teacher_required
def create():
    if request.method == 'POST':
        # フォームからデータを取得
        subject_name = request.form['subject_name']
        default_classroom = request.form['default_classroom']
        default_day_of_week = request.form['default_day_of_week']
        default_period = request.form['default_period']
        max_eor_value = request.form['max_eor_value']

        # データベースに新しい講義を挿入
        conn = current_app.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO subjects (teacher_id, subject_name, default_classroom, default_day_of_week, default_period, max_eor_value)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_user.id, subject_name, default_classroom, default_day_of_week, default_period, max_eor_value))
        conn.commit()
        
        flash('新しい講義が作成されました')
        return redirect(url_for('app.teacher.dashboard.dashboard'))
    
    # GETリクエストの場合、フォームを表示
    return render_template('teacher/lecture/new.html')


@lecture_bp.route('/new')
@teacher_required
def new():
    # GETリクエストの場合、フォームを表示
    return render_template('teacher/lecture/new.html')



@lecture_bp.route('/start/<int:subject_id>', methods=['GET', 'POST'])
@teacher_required
def start(subject_id):
    conn = current_app.get_db()
    cursor = conn.cursor()

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
        # フォームの値を取得し、デフォルト値がある場合はそれを使う
        new_day_of_week = request.form.get('day_of_week', default_day_of_week)
        new_period = request.form.get('period', default_period)
        new_classroom = request.form.get('classroom', default_classroom)

        # 新しい講義回データを追加
        cursor.execute('''
            INSERT INTO subject_counts (subject_id, classroom, day_of_week, period, is_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (subject_id, new_classroom, new_day_of_week, new_period, True))
        conn.commit()

        flash('イレギュラーなスケジュールで講義を開始しました')
        return redirect(url_for('app.teacher.lecture.show', subject_id=subject_id))

    # GETリクエスト時、デフォルト値を渡してフォームを表示
    return render_template(
        'teacher/lecture/start.html',
        subject_id=subject_id,
        default_day_of_week=default_day_of_week,
        default_period=default_period,
        default_classroom=default_classroom
    )



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
