from flask import Blueprint, render_template,current_app
from flask_login import login_required,current_user
from app.utils import teacher_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():

    conn = current_app.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subjects WHERE teacher_id = ?", (current_user.id))
    subjects = cursor.fetchall()

    return render_template('teacher/dashboard.html', subjects=subjects)
