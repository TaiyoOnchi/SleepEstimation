from flask import Blueprint, render_template,current_app
from flask_login import login_required,current_user
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
        WHERE sc.lecture_active = 1 AND s.teacher_id = ?
    """, (current_user.id,))
    active_sessions = cursor.fetchall()
    

    # 各セッションの開始時刻と終了時刻をdatetimeオブジェクトに変換
    for i, session in enumerate(active_sessions):
        # Rowオブジェクトを辞書に変換
        session_dict = dict(session)  # Rowを辞書に変換
        
        # 日時の変換処理
        if session_dict.get('start_time'):
            start_time = datetime.strptime(session_dict['start_time'], '%Y-%m-%d %H:%M:%S.%f')
            # 年月日時分の形式に変換（秒を省略）
            session_dict['start_time'] = start_time.strftime('%Y-%m-%d %H:%M')  # 年-月-日 時:分
        if session_dict.get('end_time'):
            end_time = datetime.strptime(session_dict['end_time'], '%Y-%m-%d %H:%M:%S.%f')
            # 年月日時分の形式に変換（秒を省略）
            session_dict['end_time'] = end_time.strftime('%Y-%m-%d %H:%M')  # 年-月-日 時:分
        
        # 辞書を新しい形式に更新
        active_sessions[i] = session_dict
        
        
    # 教員の全ての講義を取得
    cursor.execute("SELECT * FROM subjects WHERE teacher_id = ?", (current_user.id,))
    subjects = cursor.fetchall()
    

    
    return render_template('teacher/dashboard.html', subjects=subjects, active_sessions=active_sessions)
