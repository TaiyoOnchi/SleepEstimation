from flask import Blueprint
from flask import Blueprint, redirect, url_for,session
from flask_login import logout_user, login_required


from .home import home_bp
from .student import student_bp
from .teacher import teacher_bp

app_bp = Blueprint('app', __name__)



auth_bp = Blueprint('auth', __name__)
@auth_bp.route('/logout')
@login_required
def logout():
    if 'role' in session:
        session.pop('role', None)
    logout_user()  # ログアウト
    return redirect(url_for('app.home.top.top'))  # topにリダイレクト



# auth
app_bp.register_blueprint(auth_bp, url_prefix='/auth')

# home
app_bp.register_blueprint(home_bp, url_prefix='/')

# 学生用のルートを登録
app_bp.register_blueprint(student_bp, url_prefix='/student')

# 教員用のルートを登録
app_bp.register_blueprint(teacher_bp, url_prefix='/teacher')
