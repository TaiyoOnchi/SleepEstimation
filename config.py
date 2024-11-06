# config.py
import os
from dotenv import load_dotenv

# .envファイルのロード
load_dotenv()

class Config:
    # 環境変数からSECRET_KEYを読み込み。存在しない場合はデフォルト値を使用
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key') 
    SESSION_TYPE = 'filesystem'
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS")
    
