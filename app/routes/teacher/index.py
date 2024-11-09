from flask import Blueprint, render_template, redirect
from flask_login import login_required
from app.utils import teacher_required

index_bp = Blueprint('index', __name__)

@index_bp.route('/')
@teacher_required
@login_required
def index():
    return render_template('teacher/index.html')
