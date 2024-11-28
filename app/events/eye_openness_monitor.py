from flask_login import current_user, login_required
from flask import current_app
from app import socketio
from app.eye_openness import decode_image, process_image, save_eye_openness
from flask_socketio import join_room, leave_room  # join_room をインポート
from app.utils import student_required, teacher_required

# 開眼率の低下を監視するリストを初期化
low_eye_openness_count = {}

@socketio.on('teacher_join_room')
def handle_teacher_join_room():
    teacher_id = current_user.id
    room_name = f"teacher_{teacher_id}"  # ルーム名を動的に生成
    join_room(room_name)
    print(f"Teacher {teacher_id} joined the room {room_name}.")


@socketio.on('main_page_visited')
@student_required
def connect():
    print("呼び出されました")
    # ユーザーを student_number の部屋に参加させる
    student_number = current_user.student_number
    join_room(student_number)  # join_room を直接呼び出し
    
@socketio.on('disconnect')
@student_required
def handle_disconnect():
    student_number = current_user.student_number
    leave_room(student_number)  # 部屋から退出
    print(f"{student_number} は部屋を退出しました。")


@socketio.on('monitor_eye_openness')
@student_required
def monitor_eye_openness(data):  # 開眼率測定
    student_number = current_user.student_number
    # データを受け取る
    image_data = data['imageData']
    session_id = data['lectureId']
    # 画像データのデコードと処理
    frame = decode_image(image_data)
    if frame is None:
        print("エラー: 画像デコード失敗")
        return
    
    # データベースから基準値を取得
    conn = current_app.get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT right_eye_baseline, left_eye_baseline FROM students WHERE student_number = ?', (student_number,))
    user_data = cursor.fetchone()

    if not user_data:
        return

    right_eye_baseline, left_eye_baseline = user_data
    _, eye_openness = process_image(frame)
    
    if eye_openness: 
        right_eye_ratio = (eye_openness['eye_right'] / right_eye_baseline) * 100
        left_eye_ratio = (eye_openness['eye_left'] / left_eye_baseline) * 100
        
        # 小数点以下を切り捨てる
        eye_right_rounded = int(right_eye_ratio)
        eye_left_rounded = int(left_eye_ratio)
        print(f"左目開眼率: {eye_left_rounded}%, 右目開眼率: {eye_right_rounded}%")
        
        save_eye_openness(conn,session_id,eye_right_rounded, eye_left_rounded)

        # 両目の平均開眼率を計算
        avg_eye_openness = (right_eye_ratio + left_eye_ratio) / 2

        # 三回連続で開眼率が50%を下回っているか確認
        if student_number not in low_eye_openness_count:
            low_eye_openness_count[student_number] = []
        
        # 現在の開眼率が50%未満の場合、リストに追加
        if avg_eye_openness < 50:
            low_eye_openness_count[student_number].append(avg_eye_openness)
        else:
            # 50%以上であればリストをリセット
            low_eye_openness_count[student_number] = []

        # 三回連続で50%未満の場合、通知を表示
        if len(low_eye_openness_count[student_number]) >= 3:
            socketio.emit('low_eye_openness_alert', {'message': '開眼率が低下しています！姿勢を正してください。'}, room=student_number)
            low_eye_openness_count[student_number] = []  # カウンターをリセット
    else:
        print("開眼率取得失敗")
