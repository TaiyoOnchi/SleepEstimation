from flask import session, url_for
from app import socketio
from app.eye_openness import decode_image, process_image, save_baseline_to_database
from ..utils import verify_token
from flask_socketio import join_room  # join_room をインポート


@socketio.on('measure_baseline_join')
def on_join(data):
    token = data['token']
    token_data = verify_token(token)  # トークンの検証
    
    if not token_data:
        # トークンが無効な場合は、エラーメッセージを送信
        socketio.emit('measurement_complete', {
            'message': '認証エラー：トークンが無効です。再試行してください。',
            'redirect_url': url_for('app.student.measure_baseline.measure_baseline')
        }, room=token)  # 無効なトークンを持つクライアントにエラーメッセージを送信
        return
    
    join_room(token)  # トークンを使って特定のroomに参加

@socketio.on('measure_baseline')
def measure_baseline_eye_openness(data):
    token = data.get('token')  # クライアントからトークンを受け取る
    token_data = verify_token(token)  # トークンの検証

    if not token_data:
        socketio.emit('measurement_complete', {'message': '認証エラー：トークンが無効です。再試行してください。', 'redirect_url': url_for('app.student.measure_baseline.measure_baseline')}, room=token)
        return
    
    frames = data['frames']
    student_info = session.get('student_info')
    max_sum_openness = None
    best_frame = None

    for frame_data in frames:
        frame = decode_image(frame_data)
        _, eye_openness = process_image(frame)

        if eye_openness and eye_openness['eye_right'] and eye_openness['eye_left']:
            sum_openness = eye_openness['eye_right'] + eye_openness['eye_left']
            if max_sum_openness is None or sum_openness > max_sum_openness['eye_right'] + max_sum_openness['eye_left']:
                max_sum_openness = eye_openness
                best_frame = frame

    if max_sum_openness:
        print(f"左目開眼率: {max_sum_openness['eye_left']}, 右目開眼率: {max_sum_openness['eye_right']}")
        if max_sum_openness['eye_right'] >= 0.25 and max_sum_openness['eye_left'] >= 0.25:
            # 小数点第一位で丸める
            eye_right_rounded = round(max_sum_openness['eye_right'], 3)
            eye_left_rounded = round(max_sum_openness['eye_left'], 3)
            # 丸めた値をデータベースに保存
            save_baseline_to_database(best_frame, {'eye_right': eye_right_rounded, 'eye_left': eye_left_rounded}, student_info)
            
            if 'student_info' in session:
                session.pop('student_info', None)
            # 特定のクライアント（例えばstudent_infoを持つクライアント）に送信
            socketio.emit('measurement_complete', {'message': '新規登録されました。ログイン画面からログインしてください', 'redirect_url': url_for('app.student.login.login')}, room=token)
        else:
            message = '目の開眼率が低すぎるため、再測定します' if max_sum_openness else '有効な開眼率が検出されませんでした。再測定します'
            socketio.emit('measurement_complete', {'message': message, 'redirect_url': url_for('app.student.measure_baseline.measure_baseline')}, room=token)