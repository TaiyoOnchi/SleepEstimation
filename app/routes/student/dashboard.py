from flask import Blueprint, render_template
from app.utils import student_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@student_required
def dashboard():
    return render_template('student/dashboard.html')
