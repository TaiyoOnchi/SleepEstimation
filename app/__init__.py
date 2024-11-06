from flask import Flask
from flask_socketio import SocketIO
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from config import Config
from db_setup import init_db
from app.utils import load_user  # load_user関数をインポート

socketio = SocketIO()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'app.student.login.login'
login_manager.login_message = "ログインが必要です。"

from app.events import measure_baseline_eye_openness, monitor_eye_openness  # eventsモジュールから関数をインポート


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    socketio.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # login_managerにuser_loaderを登録
    @login_manager.user_loader
    def user_loader(user_id):
        return load_user(user_id)
    
    with app.app_context():
        init_db()
    
    # ルートの登録
    from app.routes import app_bp  # routesモジュールからapp_bpをインポート
    app.register_blueprint(app_bp)  # すべてのルートを含むBlueprintを登録

    return app
