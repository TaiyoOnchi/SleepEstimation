from flask import Blueprint, render_template, request, redirect, url_for, flash,session,current_app
from flask_login import login_user
from werkzeug.security import check_password_hash
from app.models import Teacher
from app.utils import handle_authenticated_user


login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    redirect_response = handle_authenticated_user()
    if redirect_response:
        return redirect_response
    
    if 'teacher_info' in session:
        session.pop('teacher_info', None)
    
    if request.method == 'POST':
        teacher_number = request.form['teacher_number']
        password = request.form['password']

        # データベースに接続
        conn = current_app.get_db()
        cursor = conn.cursor()

        # 教員番号とパスワードを確認
        cursor.execute('SELECT * FROM teachers WHERE teacher_number = ?', (teacher_number,))
        teacher_data = cursor.fetchone()

        if teacher_data:
            if check_password_hash(teacher_data[2], password):  # パスワードは3番目の要素
                teacher = Teacher(teacher_data[0], teacher_data[1], teacher_data[2], teacher_data[3], teacher_data[4])  # Teacherオブジェクトを作成
                session['role'] = 'teacher'
                login_user(teacher)  # ログイン
                flash("ログインしました", "success")
                return redirect(url_for('app.teacher.dashboard.dashboard'))  # 教員ダッシュボードにリダイレクト
            else:
                flash("教員番号かパスワードが違います。再度ログインしてください", "error")
                return redirect(url_for('app.teacher.login.login'))
        else:
            flash("教員番号かパスワードが違います。再度ログインしてください", "error")
            return redirect(url_for('app.teacher.login.login'))

    return render_template('teacher/login.html')
