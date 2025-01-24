from flask import Blueprint
from flask import Blueprint, redirect, url_for,session,current_app,flash
from flask_login import logout_user, login_required,current_user


from .home import home_bp
from .student import student_bp
from .teacher import teacher_bp

app_bp = Blueprint('app', __name__)



auth_bp = Blueprint('auth', __name__)
@auth_bp.route('/logout')
@login_required
def logout():
    if current_user.role == 'student':
        conn = current_app.get_db()
        cursor = conn.cursor()

        # ユーザーがアクティブな講義に参加中か確認
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
                                        alert_message="講義に参加中です", 
                                        alert_type="error"))
        
        
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
