from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user
from app.models import Teacher
from werkzeug.security import generate_password_hash

register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # フォームデータを取得
        teacher_number = request.form['teacher_number']
        password = request.form['password']
        last_name = request.form['last_name']
        first_name = request.form['first_name']
        kana_last_name = request.form['kana_last_name']
        kana_first_name = request.form['kana_first_name']

        # パスワード強度チェック
        is_valid, message = is_strong_password(password)
        if not is_valid:
            flash(message)
            # 入力情報をsessionに保存
            session['teacher_info'] = {
                'teacher_number': teacher_number,
                'last_name': last_name,
                'first_name': first_name,
                'kana_last_name': kana_last_name,
                'kana_first_name': kana_first_name
            }
            return redirect(url_for('app.teacher.register.register'))

        # パスワードのハッシュ化
        hashed_password = generate_password_hash(password)

        # データベースに接続
        conn = current_app.get_db()
        cursor = conn.cursor()

        # 既に教員が存在するかチェック
        cursor.execute('SELECT * FROM teachers WHERE teacher_number = ?', (teacher_number,))
        existing_teacher = cursor.fetchone()

        if existing_teacher:
            flash("その教員番号は既に登録されています。")
            # 入力情報をsessionに保存
            session['teacher_info'] = {
                'teacher_number': teacher_number,
                'last_name': last_name,
                'first_name': first_name,
                'kana_last_name': kana_last_name,
                'kana_first_name': kana_first_name
            }
            return redirect(url_for('app.teacher.register.register'))

        # 教員情報を登録
        cursor.execute('''
            INSERT INTO teachers (teacher_number, password, last_name, first_name, kana_last_name, kana_first_name)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (teacher_number, hashed_password, last_name, first_name, kana_last_name, kana_first_name))
        
        cursor.execute('SELECT * FROM teachers WHERE teacher_number = ?', (teacher_number,))
        teacher_data = cursor.fetchone()

        conn.commit()
        
        
        # 正常に登録された場合、sessionから入力情報を削除
        session.pop('teacher_info', None)
        
        # 登録完了メッセージとユーザーのログイン処理
        flash("教員が登録されました。")
        teacher = Teacher(teacher_data[0], teacher_data[1], teacher_data[2], teacher_data[3], teacher_data[4])  # Teacherオブジェクトを作成
        session['role'] = 'teacher'
        login_user(teacher)
        return redirect(url_for('app.teacher.dashboard.dashboard'))

    # セッションに保存されている情報を渡して、登録画面を表示
    teacher_info = session.get('teacher_info', {})
    return render_template('teacher/register.html', teacher_info=teacher_info)

# パスワードのバリデーション
def is_strong_password(password):
    if len(password) < 6:  # パスワードが6文字以上か確認
        return False, "パスワードは6文字以上で入力してください。"
    return True, ""
