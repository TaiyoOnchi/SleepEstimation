from itsdangerous import URLSafeTimedSerializer
from config import Config

# トークンを生成・検証するためのシリアライザを設定
serializer = URLSafeTimedSerializer(Config.SECRET_KEY)

def generate_token(data):
    """アクセストークンを生成"""
    return serializer.dumps(data, salt=Config.SECRET_KEY)

def verify_token(token):
    """アクセストークンを検証"""
    try:
        data = serializer.loads(token, salt=Config.SECRET_KEY, max_age=300) # 有効期限n秒
        return data
    except:
        return None
