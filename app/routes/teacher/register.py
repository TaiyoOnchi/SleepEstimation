from flask import Blueprint, render_template, request, redirect, url_for, flash,session
from flask_login import login_user
from app.models import Teacher
from werkzeug.security import generate_password_hash
from app.utils import get_db_connection

register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        teacher_number = request.form['teacher_number']
        password = generate_password_hash(request.form['password'])
        last_name = request.form['last_name']
        first_name = request.form['first_name']
        kana_last_name = request.form['kana_last_name']
        kana_first_name = request.form['kana_first_name']

        # データベースに接続
        conn = get_db_connection()
        cursor = conn.cursor()

        # 既に教員が存在するかチェック
        cursor.execute('SELECT * FROM teachers WHERE teacher_number = ?', (teacher_number,))
        existing_teacher = cursor.fetchone()

        if existing_teacher:
            flash("その教員番号は既に登録されています。")
            return redirect(url_for('app.teacher.register.register'))

        # 教員情報を登録
        cursor.execute('''
            INSERT INTO teachers (teacher_number, password, last_name, first_name, kana_last_name, kana_first_name)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (teacher_number, password, last_name, first_name, kana_last_name, kana_first_name))
        
        cursor.execute('SELECT * FROM teachers WHERE teacher_number = ?', (teacher_number,))
        teacher_data = cursor.fetchone()

        conn.commit()
        conn.close()
        
        # 登録完了メッセージ
        flash("教員が登録されました。")
        teacher = Teacher(teacher_data[0], teacher_data[1], teacher_data[2], teacher_data[3], teacher_data[4])  # Teacherオブジェクトを作成
        session['role'] = 'teacher'
        login_user(teacher)
        return redirect(url_for('app.teacher.dashboard.dashboard'))

    return render_template('teacher/register.html')
