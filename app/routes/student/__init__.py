# app/student/__init__.py
from flask import Blueprint

from .dashboard import dashboard_bp
from .main import main_bp
from .register import register_bp
from .measure_baseline import measure_baseline_bp
from .login import login_bp
from .show import show_bp
from .lecture import lecture_bp
from .errors import error_bp

student_bp = Blueprint('student', __name__)

# 各Blueprintを登録
student_bp.register_blueprint(dashboard_bp)
student_bp.register_blueprint(main_bp)
student_bp.register_blueprint(register_bp)
student_bp.register_blueprint(measure_baseline_bp)
student_bp.register_blueprint(login_bp)
student_bp.register_blueprint(show_bp)
student_bp.register_blueprint(lecture_bp)
student_bp.register_blueprint(error_bp)
