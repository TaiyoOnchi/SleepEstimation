from flask import Blueprint, render_template
from app.utils import handle_authenticated_user

top_bp = Blueprint('top', __name__)

@top_bp.route('/')
def top():
    redirect_response = handle_authenticated_user()
    if redirect_response:
        return redirect_response
    return render_template('home/top.html')
