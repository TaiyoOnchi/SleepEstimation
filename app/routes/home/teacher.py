from flask import Blueprint, render_template, redirect, url_for, session
from flask_login import current_user
from app.utils import handle_authenticated_user

teacher_top_bp = Blueprint('teacher_top', __name__)

@teacher_top_bp.route('/teacher_top')
def teacher_top():
    redirect_response = handle_authenticated_user()
    if redirect_response:
        return redirect_response
    return render_template('home/teacher.html')
