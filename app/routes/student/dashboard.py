from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.utils import student_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@student_required
def dashboard():
    return render_template('student/dashboard.html')
