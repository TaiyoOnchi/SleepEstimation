from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.utils import student_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    if current_user.is_authenticated and current_user.role == 'student':
        return render_template('student/dashboard.html')
    flash('学生でログインしてください')
    return redirect(url_for('student.login'))
