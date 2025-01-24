from functools import wraps
from flask import redirect, url_for, flash,current_app
from flask_login import current_user
from flask_login import login_required


def student_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'student':
            flash("生徒専用ページです。","error")
            return redirect(url_for("app.teacher.dashboard.dashboard"))  # 教員ダッシュボードにリダイレクト
        
        # 現在の関数名を取得
        current_function_name = f.__name__
        
        # main関数,connect(room参加)関数以外の場合にアクティブな講義の確認を行う
        if current_function_name not in ['main', 'connect','monitor_eye_openness','adjust_baseline','handle_low_eye_openness_response']:
            
            # 学生が他のアクティブな講義に参加中か確認
            conn = current_app.get_db()
            cursor = conn.cursor()
            
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

        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'teacher':
            flash("教員専用ページです。","error")
            return redirect(url_for("app.student.dashboard.dashboard"))  # 生徒ダッシュボードにリダイレクト

        return f(*args, **kwargs)
    return decorated_function


def handle_authenticated_user():
    if current_user.is_authenticated:
        flash('既にログインしています。',"error")
        if current_user.role == 'student':
            return redirect(url_for('app.student.dashboard.dashboard'))
        else:
            return redirect(url_for('app.teacher.dashboard.dashboard'))