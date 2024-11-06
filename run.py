from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    from app import create_app  # 遅延インポート
    app = create_app()
    app.run(ssl_context=('cert.pem', 'key.pem'), host='0.0.0.0')
