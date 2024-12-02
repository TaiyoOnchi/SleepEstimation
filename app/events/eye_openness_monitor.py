from flask_login import current_user, login_required
from flask import current_app
from app import socketio
from app.eye_openness import decode_image, process_image, save_eye_openness
from flask_socketio import join_room, leave_room  # join_room をインポート
from app.utils import student_required, teacher_required



@socketio.on('teacher_join_room')
def handle_teacher_join_room():
    teacher_id = current_user.id
    room_name = f"teacher_{teacher_id}"  # ルーム名を動的に生成
    join_room(room_name)
    print(f"Teacher {teacher_id} joined the room {room_name}.")


@socketio.on('student_join_room')
@student_required
def connect():
    print("呼び出されました")
    # ユーザーを student_number の部屋に参加させる
    student_number = current_user.student_number
    join_room(student_number)  # join_room を直接呼び出し
    
@socketio.on('disconnect')
@login_required
def handle_disconnect():
    # ログインしているユーザーが学生の場合
    if current_user.role == 'student':
        student_number = current_user.student_number
        leave_room(student_number)  # 学生の部屋から退出
        print(f"学生 {student_number} は部屋を退出しました。")
        
        # # 必要に応じて学生の退出時の処理を追加
        # # 例: データベースに退席時刻を記録するなど
        # conn = current_app.get_db()
        # cursor = conn.cursor()
        # cursor.execute('''
        #     UPDATE student_participations
        #     SET exit_time = ?
        #     WHERE student_number = ? AND exit_time IS NULL
        # ''', (datetime.now(), student_number))
        # conn.commit()

    # ログインしているユーザーが教員の場合
    elif current_user.role == 'teacher':
        teacher_id = current_user.id
        room_name = f"teacher_{teacher_id}"  # 教員のルーム名
        leave_room(room_name)  # 教員の部屋から退出
        print(f"教員 {teacher_id} は部屋を退出しました。")


    else:
        # ユーザーがログインしていない、または不明なタイプの場合
        print("未確認のユーザーが接続を切断しました。")


# 開眼率の低下を監視するリストを初期化
low_eye_openness_count = {}
failed_eye_openness_count = {}  # 開眼率取得失敗の回数を追跡する辞書

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
    # データベースから基準値とero_thresholdを取得
    cursor.execute('''
        SELECT s.right_eye_baseline, s.left_eye_baseline, sub.ero_threshold
        FROM students s
        JOIN student_subjects ss ON s.id = ss.student_id
        JOIN subjects sub ON ss.subject_id = sub.id
        JOIN student_participations sp ON ss.id = sp.student_subject_id
        WHERE s.student_number = ? AND sp.id = ?
    ''', (student_number, session_id))
    user_data = cursor.fetchone()

    if not user_data:
        return

    right_eye_baseline, left_eye_baseline, ero_threshold = user_data
    _, eye_openness = process_image(frame)

    # 学生が辞書に存在しない場合の初期化
    if student_number not in low_eye_openness_count:
        low_eye_openness_count[student_number] = []
    if student_number not in failed_eye_openness_count:
        failed_eye_openness_count[student_number] = 0

    if eye_openness: 
        right_eye_ratio = (eye_openness['eye_right'] / right_eye_baseline) * 100
        left_eye_ratio = (eye_openness['eye_left'] / left_eye_baseline) * 100
        
        # 小数点以下を切り捨てる
        eye_right_rounded = int(right_eye_ratio)
        eye_left_rounded = int(left_eye_ratio)
        print(f"左目開眼率: {eye_left_rounded}%, 右目開眼率: {eye_right_rounded}%")
        
        save_eye_openness(conn, session_id, eye_right_rounded, eye_left_rounded)

        # 両目の平均開眼率を計算
        avg_eye_openness = (right_eye_ratio + left_eye_ratio) / 2
        socketio.emit('eye_openness_update', {
            'avgEyeOpenness': avg_eye_openness,
            'eroThreshold': ero_threshold
        }, room=student_number)

        # 現在の開眼率が50%未満の場合、リストに追加
        if avg_eye_openness < ero_threshold:
            low_eye_openness_count[student_number].append(avg_eye_openness)
        else:
            # 50%以上であればリストをリセット
            low_eye_openness_count[student_number] = []

        # 三回連続で50%未満の場合、通知を表示
        if len(low_eye_openness_count[student_number]) >= 3:
            socketio.emit('low_eye_openness_alert', {'message': '開眼率が低下しています！姿勢を正してください。'}, room=student_number)
            low_eye_openness_count[student_number] = []  # カウンターをリセット

        # 開眼率取得失敗カウンターをリセット
        failed_eye_openness_count[student_number] = 0

    else:
        print("開眼率取得失敗")
        # 開眼率取得失敗時のカウントをインクリメント
        failed_eye_openness_count[student_number] += 1

        # 開眼率取得失敗が5回連続の場合、通知を送信
        if failed_eye_openness_count[student_number] >= 5:
            socketio.emit('low_eye_openness_alert', {'message': '開眼率の検出に失敗しています。カメラの状態を確認してください。'}, room=student_number)
            
        # 開眼率取得失敗が10回連続の場合、通知を送信
        if failed_eye_openness_count[student_number] >= 10:
            socketio.emit('low_eye_openness_alert', {'message': '開眼率が検出できません、注意回数が記録されました'}, room=student_number)
            failed_eye_openness_count[student_number] = 0  # カウンターをリセット
