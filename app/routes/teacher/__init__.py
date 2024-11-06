from flask import Blueprint

from .index import index_bp
from .register import register_bp
from .login import login_bp
from .dashboard import dashboard_bp
# from .errors import error_bp

teacher_bp = Blueprint('teacher', __name__)

# 各Blueprintを登録
teacher_bp.register_blueprint(index_bp)
teacher_bp.register_blueprint(register_bp)
teacher_bp.register_blueprint(login_bp)
teacher_bp.register_blueprint(dashboard_bp)
# teacher_bp.register_blueprint(error_bp)
