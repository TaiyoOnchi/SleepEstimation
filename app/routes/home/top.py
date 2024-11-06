from flask import Blueprint, render_template, redirect, url_for, session
from flask_login import current_user
from app.utils import handle_authenticated_user

top_bp = Blueprint('top', __name__)

@top_bp.route('/')
def top():
    redirect_response = handle_authenticated_user()
    if redirect_response:
        return redirect_response
    return render_template('home/top.html')
