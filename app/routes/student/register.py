from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from app.utils import get_db_connection

register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_number = request.form['student_number']
        password = generate_password_hash(request.form['password'])
        last_name = request.form['last_name']
        first_name = request.form['first_name']
        kana_last_name = request.form['kana_last_name']
        kana_first_name = request.form['kana_first_name']
        gender = request.form['gender']

        conn = get_db_connection()
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
