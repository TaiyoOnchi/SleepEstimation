from flask import Blueprint, render_template
from flask_login import login_required,current_user
from app.utils import teacher_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    print(f"Current user role: {current_user.role}", flush=True)
    return render_template('/teacher/dashboard.html')
