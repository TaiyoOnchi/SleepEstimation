# app/student/__init__.py
from flask import Blueprint

from .top import top_bp
from .teacher import teacher_top_bp


home_bp = Blueprint('home', __name__)

# 各Blueprintを登録
home_bp.register_blueprint(top_bp)
home_bp.register_blueprint(teacher_top_bp)

