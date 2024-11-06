from flask_login import current_user
from app import socketio
import sqlite3
from app.eye_openness import decode_image, process_image,save_eye_openness
from app.utils.database import get_db_connection


@socketio.on('monitor_eye_openness')
def monitor_eye_openness(image_data): # 開眼率測定
    student_number = current_user.student_number
    
    # 画像データのデコードと処理
    frame = decode_image(image_data)

    if frame is None:
        print("エラー: 画像データのデコードに失敗しました")
        return
    
    # データベースから基準値を取得
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT right_eye_baseline, left_eye_baseline FROM students WHERE student_number = ?', (student_number,))
    user_data = cursor.fetchone()
    conn.close()

    if not user_data:
        return

    right_eye_baseline, left_eye_baseline = user_data
    _, eye_openness = process_image(frame)

    if eye_openness: 
        right_eye_ratio = (eye_openness['eye_right'] / right_eye_baseline) * 100
        left_eye_ratio = (eye_openness['eye_left'] / left_eye_baseline) * 100
        save_eye_openness(student_number, right_eye_ratio, left_eye_ratio)

        # # 画像に開眼率を表示（右目と左目の開眼率をテキストとして描画）
        # cv.putText(frame, f'Right Eye: {right_eye_ratio:.2f}%', (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        # cv.putText(frame, f'Left Eye: {left_eye_ratio:.2f}%', (10, 60), cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # # 画像をエンコードしてWeb経由で送信
        # _, buffer = cv.imencode('.jpg', frame)
        # frame_data = base64.b64encode(buffer).decode('utf-8')
        # socketio.emit('image_update', frame_data)
        print(right_eye_ratio,left_eye_ratio)
    else:
        print("開眼率取得失敗")