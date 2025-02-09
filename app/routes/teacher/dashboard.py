from flask import Blueprint, render_template, current_app
from flask_login import current_user
from app.utils import teacher_required
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@teacher_required
def dashboard():
    conn = current_app.get_db()
    cursor = conn.cursor()
    
    # 現在アクティブな講義（開講中の講義）を取得
    cursor.execute("""
        SELECT sc.*, s.subject_name
        FROM subject_counts sc
        JOIN subjects s ON sc.subject_id = s.id
        WHERE sc.end_time IS NULL AND s.teacher_id = ?
    """, (current_user.id,))
    active_sessions = cursor.fetchall()
    
    # 講義が1つだけの場合は、辞書に変換して単一のセッションとして扱う
    active_session = None
    if len(active_sessions) == 1:
        # Rowオブジェクトを辞書に変換
        active_session = dict(active_sessions[0])
        
        # 日時の変換処理
        if active_session.get('start_time'):
            start_time = datetime.strptime(active_session['start_time'], '%Y-%m-%d %H:%M:%S.%f')
            active_session['start_time'] = start_time.strftime('%Y-%m-%d %H:%M')  # 年-月-日 時:分
        if active_session.get('end_time'):
            end_time = datetime.strptime(active_session['end_time'], '%Y-%m-%d %H:%M:%S.%f')
            active_session['end_time'] = end_time.strftime('%Y-%m-%d %H:%M')  # 年-月-日 時:分
    
    # 教員の全ての講義を取得
    cursor.execute("SELECT * FROM subjects WHERE teacher_id = ?", (current_user.id,))
    subjects = cursor.fetchall()
    print(active_session)
    
    return render_template('teacher/dashboard.html', subjects=subjects, active_session=active_session)
