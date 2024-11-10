from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user
from flask_login import login_required


def student_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'student':
            flash("生徒専用ページです。")
            return redirect(url_for("app.teacher.dashboard.dashboard"))  # 教員ダッシュボードにリダイレクト

        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'teacher':
            flash("教員専用ページです。")
            return redirect(url_for("app.student.dashboard.dashboard"))  # 生徒ダッシュボードにリダイレクト

        return f(*args, **kwargs)
    return decorated_function


def handle_authenticated_user():
    if current_user.is_authenticated:
        flash('既にログインしています。')
        if current_user.role == 'student':
            return redirect(url_for('app.student.dashboard.dashboard'))
        else:
            return redirect(url_for('app.teacher.dashboard.dashboard'))