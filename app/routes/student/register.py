from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import generate_password_hash


register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = request.form.get('password')
        is_valid, message = is_strong_password(password)
        if not is_valid:
            flash(message)  # Flaskでエラーメッセージを表示
            return redirect(url_for('app.student.register.register'))  # サインアップ画面に戻る
        else:
            # パスワードが強力であれば、そのままハッシュ化して保存
            hashed_password = generate_password_hash(password)
        
        student_number = request.form['student_number']
        password = hashed_password
        is_valid, message = is_strong_password(password)
        last_name = request.form['last_name']
        first_name = request.form['first_name']
        kana_last_name = request.form['kana_last_name']
        kana_first_name = request.form['kana_first_name']
        gender = request.form['gender']

        conn = current_app.get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students WHERE student_number = ?', (student_number,))
        existing_user = cursor.fetchone()
        conn.close()

        if existing_user:
            flash("その学籍番号は既に登録されています。")
            return redirect(url_for('app.student.register.register'))

        session['student_info'] = {
            'student_number': student_number,
            'password': password,
            'last_name': last_name,
            'first_name': first_name,
            'kana_last_name': kana_last_name,
            'kana_first_name': kana_first_name,
            'gender': gender
        }

        return redirect(url_for('app.student.measure_baseline.measure_baseline'))

    return render_template('student/register.html')


# passwordのバリデーション
def is_strong_password(password):
    if len(password) < 6: #8文字以上
        return False, "パスワードを6文字以上にしてください"
    return True, ""
