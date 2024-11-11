from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import generate_password_hash

register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # フォームデータを取得
        student_number = request.form['student_number']
        last_name = request.form['last_name']
        first_name = request.form['first_name']
        kana_last_name = request.form['kana_last_name']
        kana_first_name = request.form['kana_first_name']
        gender = request.form['gender']
        password = request.form.get('password')

        # パスワードのバリデーション
        is_valid, message = is_strong_password(password)
        if not is_valid:
            flash(message)
            # 入力情報をsessionに保存
            session['student_info'] = {
                'student_number': student_number,
                'last_name': last_name,
                'first_name': first_name,
                'kana_last_name': kana_last_name,
                'kana_first_name': kana_first_name,
                'gender': gender
            }
            return redirect(url_for('app.student.register.register'))

        # パスワードのハッシュ化
        hashed_password = generate_password_hash(password)

        conn = current_app.get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students WHERE student_number = ?', (student_number,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("その学籍番号は既に登録されています。")
            # 入力情報をsessionに保存
            session['student_info'] = {
                'student_number': student_number,
                'last_name': last_name,
                'first_name': first_name,
                'kana_last_name': kana_last_name,
                'kana_first_name': kana_first_name,
                'gender': gender
            }
            return redirect(url_for('app.student.register.register'))

        # 正常に登録された場合、sessionから入力情報を削除し、新しい情報を追加
        session.pop('student_info', None)
        session['student_info'] = {
            'student_number': student_number,
            'password': hashed_password,
            'last_name': last_name,
            'first_name': first_name,
            'kana_last_name': kana_last_name,
            'kana_first_name': kana_first_name,
            'gender': gender
        }

        return redirect(url_for('app.student.measure_baseline.measure_baseline'))

    # セッションに保存されている情報を渡して、サインアップ画面を表示
    student_info = session.get('student_info', {})
    return render_template('student/register.html', student_info=student_info)

# passwordのバリデーション
def is_strong_password(password):
    if len(password) < 6: #8文字以上
        return False, "パスワードを6文字以上にしてください"
    return True, ""
