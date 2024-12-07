from flask_login import current_user, login_required
from flask import current_app
from app import socketio
from app.eye_openness import decode_image, process_image, save_eye_openness
from flask_socketio import join_room, leave_room  # join_room をインポート
from app.utils import student_required, teacher_required
from datetime import datetime





@socketio.on('teacher_join_room')
@teacher_required
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
sleep_start_time = {} # 居眠り開始タイムスタンプを記録する辞書


@socketio.on('monitor_eye_openness')
@student_required
def monitor_eye_openness(data):  # 開眼率測定
    student_number = current_user.student_number
    # データを受け取る
    image_data = data['imageData']
    participation_id = data['student_participation_id']
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
    ''', (student_number, participation_id))
    user_data = cursor.fetchone()

    if not user_data:
        return

    right_eye_baseline, left_eye_baseline, ero_threshold = user_data
    _, eye_openness = process_image(frame)

    # 学生が辞書に存在しない場合の初期化
    if student_number not in low_eye_openness_count:
        low_eye_openness_count[student_number] = 0
    if student_number not in failed_eye_openness_count:
        failed_eye_openness_count[student_number] = 0

    if eye_openness: 
        failed_eye_openness_count[student_number] = 0  # カウンターをリセット
        right_eye_ratio = (eye_openness['eye_right'] / right_eye_baseline) * 100
        left_eye_ratio = (eye_openness['eye_left'] / left_eye_baseline) * 100
        
        # 小数点以下を切り捨てる
        eye_right_rounded = int(right_eye_ratio)
        eye_left_rounded = int(left_eye_ratio)
        print(f"左目開眼率: {eye_left_rounded}%, 右目開眼率: {eye_right_rounded}%")
        
        save_eye_openness(conn, participation_id, eye_right_rounded, eye_left_rounded)

        # 両目の平均開眼率を計算
        avg_eye_openness = (right_eye_ratio + left_eye_ratio) / 2
        socketio.emit('eye_openness_update', {
            'avgEyeOpenness': avg_eye_openness,
            'eroThreshold': ero_threshold
        }, room=student_number)

        
        if avg_eye_openness < ero_threshold: # 現在の開眼率が閾値未満の場合、リストに追加
            low_eye_openness_count[student_number] += 1
            
        
        else: # 閾値以上であればリストをリセット
            low_eye_openness_count[student_number] = 0
            
            if student_number in sleep_start_time:
                # 居眠り終了時刻を取得
                sleep_end_time = datetime.now()
                sleep_duration = (sleep_end_time - sleep_start_time[student_number]).total_seconds()

                # sleep_time を更新
                cursor.execute('''
                    UPDATE attentions
                    SET sleep_time = TIME(STRFTIME('%H:%M:%S', sleep_time, '+' || ? || ' seconds'))
                    WHERE student_participation_id = ? AND timestamp = ?
                ''', (int(sleep_duration), participation_id, sleep_start_time[student_number]))
                conn.commit()

                # 記録リセット
                sleep_start_time.pop(student_number, None)
                low_eye_openness_count[student_number] = 0  # カウンターをリセット
                failed_eye_openness_count[student_number] = 0  # カウンターをリセット
                
            


        # 三回連続で閾値以下の場合、通知を表示
        if low_eye_openness_count[student_number] == 3:
            socketio.emit('low_eye_openness_alert', {'message': '開眼率が低下しています！姿勢を正してください。'}, room=student_number)
        
        elif low_eye_openness_count[student_number] == 6:
            # 注意回数が記録された際の処理
            cursor.execute('''
                UPDATE student_subjects
                SET total_attentions = total_attentions + 1
                WHERE id = (
                    SELECT ss.id 
                    FROM student_subjects ss
                    JOIN student_participations sp ON ss.id = sp.student_subject_id
                    WHERE sp.id = ?
                )
            ''', (participation_id,))
            
            cursor.execute('''
                UPDATE student_participations
                SET attention_count = attention_count + 1
                WHERE id = ?
            ''', (participation_id,))
            
            sleep_start_time[student_number] = datetime.now()
            
            # attentions テーブルに新しいレコードを挿入
            cursor.execute('''
                INSERT INTO attentions (student_participation_id, timestamp)
                VALUES (?, ?)
            ''', (participation_id, sleep_start_time[student_number]))

            conn.commit()  # 変更を保存
            
            # 学生向け通知
            socketio.emit('low_eye_openness_alert', {'message': '開眼率が連続して低下していたため、注意回数が記録されました。'}, room=student_number)
            
            # 教員向け通知
            teacher_id = get_teacher_id_by_participation_id(participation_id)  # 関連する教員IDを取得する関数を実装
            
            if teacher_id:
                teacher_room = f"teacher_{teacher_id}"
                socketio.emit('attention_updated', {
                    'student_number': student_number,
                    'attention_count': get_attention_count(participation_id)  # 現在の注意回数を取得
                }, room=teacher_room)





    else:
        print("開眼率取得失敗")
        # 開眼率取得失敗時のカウントをインクリメント
        failed_eye_openness_count[student_number] += 1

        # 開眼率取得失敗が5回連続の場合、通知を送信
        if failed_eye_openness_count[student_number] == 5:
            socketio.emit('low_eye_openness_alert', {'message': '開眼率の検出に失敗しています。カメラの状態を確認してください。'}, room=student_number)
            
        # 開眼率取得失敗が10回連続の場合、通知を送信
        elif failed_eye_openness_count[student_number] == 10:
            
            # 注意回数が記録された際の処理
            cursor.execute('''
                UPDATE student_subjects
                SET total_attentions = total_attentions + 1
                WHERE id = (
                    SELECT ss.id 
                    FROM student_subjects ss
                    JOIN student_participations sp ON ss.id = sp.student_subject_id
                    WHERE sp.id = ?
                )
            ''', (participation_id,))
            
            cursor.execute('''
                UPDATE student_participations
                SET attention_count = attention_count + 1
                WHERE id = ?
            ''', (participation_id,))
            
            sleep_start_time[student_number] = datetime.now()
            
            # attentions テーブルに新しいレコードを挿入
            cursor.execute('''
                INSERT INTO attentions (student_participation_id, timestamp)
                VALUES (?, ?)
            ''', (participation_id, sleep_start_time[student_number]))

            conn.commit()  # 変更を保存
            
            # 学生向け通知
            socketio.emit('low_eye_openness_alert', {'message': '開眼率が検出できません、注意回数が記録されました'}, room=student_number)            
            
            # 教員向け通知
            teacher_id = get_teacher_id_by_participation_id(participation_id)  # 関連する教員IDを取得する関数を実装
            if teacher_id:
                teacher_room = f"teacher_{teacher_id}"
                socketio.emit('attention_updated', {
                    'student_number': student_number,
                    'attention_count': get_attention_count(participation_id)  # 現在の注意回数を取得
                }, room=teacher_room)




def get_teacher_id_by_participation_id(participation_id):
    conn = current_app.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.id
        FROM teachers t
        JOIN subjects sub ON t.id = sub.teacher_id
        JOIN student_subjects ss ON sub.id = ss.subject_id
        JOIN student_participations sp ON ss.id = sp.student_subject_id
        WHERE sp.id = ?
    ''', (participation_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_attention_count(participation_id):
    conn = current_app.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT attention_count
        FROM student_participations
        WHERE id = ?
    ''', (participation_id,))
    result = cursor.fetchone()
    return result[0] if result else 0
