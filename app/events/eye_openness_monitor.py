from flask_login import current_user, login_required
from flask import current_app
from app import socketio
from app.eye_openness import decode_image, process_image, save_eye_openness
from flask_socketio import join_room, leave_room  # join_room をインポート
from app.utils import student_required, teacher_required
from datetime import datetime
import base64
import cv2 as cv





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
decode_fail_count = {}
low_eye_openness_count = {}
failed_eye_openness_count = {}  # 開眼率取得失敗の回数を追跡する辞書
sleep_start_time = {} # 居眠り開始タイムスタンプを記録する辞書


import time

@socketio.on('monitor_eye_openness')
@student_required
def monitor_eye_openness(data):  # 開眼率測定
    cycle_start = time.perf_counter()  # サイクル開始時刻を記録
    student_number = current_user.student_number
    # データを受け取る
    image_data = data['imageData']
    participation_id = data['student_participation_id']
    # 画像データのデコードと処理
    frame = decode_image(image_data)
    if frame is None:
        print("エラー: 画像デコード失敗")
        
        # 開眼率取得失敗時のカウントをインクリメント
        if student_number not in decode_fail_count:
            decode_fail_count[student_number] = 0
        decode_fail_count[student_number] += 1
        
        # 注意回数記録通知（1分半連続で失敗）
        if decode_fail_count[student_number] == 30 and student_number not in sleep_start_time:
            conn = current_app.get_db()
            cursor = conn.cursor()
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
                INSERT INTO attentions (student_participation_id, timestamp, reason)
                VALUES (?, ?, ?)
            ''', (participation_id, sleep_start_time[student_number], 2))
            conn.commit()
            
            # 学生向け通知
            socketio.emit('eye_openness_alert', {
                'message': 'カメラが検出できなかったため、注意回数が記録されました。'
            }, room=student_number)
            
            # 教員向け通知
            teacher_id = get_teacher_id_by_participation_id(participation_id)
            if teacher_id:
                teacher_room = f"teacher_{teacher_id}"
                socketio.emit('attention_updated', {
                    'student_number': student_number,
                    'attention_count': get_attention_count(participation_id)
                }, room=teacher_room)
                
        # カメラアクセス失敗通知（30秒連続で通知）
        elif decode_fail_count[student_number] > 0 and decode_fail_count[student_number] % 15 == 0:
            socketio.emit('eye_openness_alert', {
                'message': 'カメラにアクセスできません。\nブラウザの設定でカメラアクセスを許可してください。'
            }, room=student_number)
        
        # サイクル終了時の計測結果を出力して終了
        cycle_end = time.perf_counter()
        cycle_time = cycle_end - cycle_start
        print("サイクル処理時間: {:.3f}秒, 周波数: {:.2f}Hz".format(cycle_time, 1/cycle_time if cycle_time else 0))
        return
    
    # フレーム処理
    processed_frame, eye_openness = process_image(frame)

    # フレームをJPEGにエンコード
    _, buffer = cv.imencode('.jpg', processed_frame)
    frame_base64 = base64.b64encode(buffer).decode('utf-8')

    # クライアントに送信
    socketio.emit('processed_frame', {'image': frame_base64}, room=student_number)

    # デコード成功時はカウントをリセット
    decode_fail_count[student_number] = 0
    
    # データベースから基準値を取得
    conn = current_app.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.right_eye_baseline, s.left_eye_baseline, sub.eor_threshold
        FROM students s
        JOIN student_subjects ss ON s.id = ss.student_id
        JOIN subjects sub ON ss.subject_id = sub.id
        JOIN student_participations sp ON ss.id = sp.student_subject_id
        WHERE s.student_number = ? AND sp.id = ?
    ''', (student_number, participation_id))
    user_data = cursor.fetchone()

    if not user_data:
        cycle_end = time.perf_counter()
        cycle_time = cycle_end - cycle_start
        print("サイクル処理時間: {:.3f}秒, 周波数: {:.2f}Hz".format(cycle_time, 1/cycle_time if cycle_time else 0))
        return

    right_eye_baseline, left_eye_baseline, eor_threshold = user_data
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

        # 両目の最大開眼率を計算
        max_eye_openness = max(right_eye_ratio, left_eye_ratio)
        socketio.emit('eye_openness_update', {
            'maxEyeOpenness': max_eye_openness,
            'eorThreshold': eor_threshold
        }, room=student_number)

        if max_eye_openness < eor_threshold:  # 現在の開眼率が閾値未満の場合、リストに追加
            low_eye_openness_count[student_number] += 1
            
        else:  # 閾値以上であればリストをリセット
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
                
        if low_eye_openness_count[student_number] == 10 and student_number not in sleep_start_time:
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
                INSERT INTO attentions (student_participation_id, timestamp, reason)
                VALUES (?, ?, ?)
            ''', (participation_id, sleep_start_time[student_number], 0))
            # 挿入したレコードの ID を取得
            new_attention_id = cursor.lastrowid

            conn.commit()  # 変更を保存
            
            # 学生向け通知
            socketio.emit('eye_openness_alert', {
                'message': '開眼率が連続して低下していたため、\n注意回数が記録されました。\n(誤検出の場合、画面で操作してください)'
            }, room=student_number)
            # low_eye_openness_warning に新しい attentions ID を渡す
            socketio.emit('low_eye_openness_warning', {'attention_id': new_attention_id}, room=student_number)
            
            # 教員向け通知
            teacher_id = get_teacher_id_by_participation_id(participation_id)
            if teacher_id:
                teacher_room = f"teacher_{teacher_id}"
                socketio.emit('attention_updated', {
                    'student_number': student_number,
                    'attention_count': get_attention_count(participation_id)
                }, room=teacher_room)
                
        # 連続で閾値以下の場合、通知を表示
        elif low_eye_openness_count[student_number] > 0 and low_eye_openness_count[student_number] % 5 == 0:
            socketio.emit('eye_openness_alert', {'message': '開眼率が低下しています！'}, room=student_number)

    else:
        print("開眼率取得失敗")
        # 開眼率取得失敗時のカウントをインクリメント
        failed_eye_openness_count[student_number] += 1
        socketio.emit('eye_openness_update', {
            'avgEyeOpenness': None,  # 測定できない場合はNullを送信
            'eorThreshold': eor_threshold
        }, room=student_number)

        # 開眼率取得失敗が連続の場合、通知を送信
        if failed_eye_openness_count[student_number] == 30 and student_number not in sleep_start_time:
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
            
            cursor.execute('''
                INSERT INTO attentions (student_participation_id, timestamp, reason)
                VALUES (?, ?, ?)
            ''', (participation_id, sleep_start_time[student_number], 1))
            conn.commit()
            
            socketio.emit('eye_openness_alert', {'message': '目が検出できなかったため、注意回数が記録されました'}, room=student_number)            
            
            teacher_id = get_teacher_id_by_participation_id(participation_id)
            if teacher_id:
                teacher_room = f"teacher_{teacher_id}"
                socketio.emit('attention_updated', {
                    'student_number': student_number,
                    'attention_count': get_attention_count(participation_id)
                }, room=teacher_room)
                
        elif failed_eye_openness_count[student_number] > 0 and failed_eye_openness_count[student_number] % 15 == 0:
            socketio.emit('eye_openness_alert', {
                'message': '開眼率の検出に失敗しています。\nカメラの状態を確認してください。'
            }, room=student_number)
    
    # サイクル終了時の計測結果を出力
    cycle_end = time.perf_counter()
    cycle_time = cycle_end - cycle_start
    print("サイクル処理時間: {:.3f}秒, 周波数: {:.2f}Hz".format(cycle_time, 1/cycle_time if cycle_time else 0))



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




@socketio.on('adjust_baseline')
@student_required
def adjust_baseline(data):
    if data['adjust'] == 'yes':
        student_number = current_user.student_number
        conn = current_app.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE students
            SET right_eye_baseline = right_eye_baseline * 0.95,
                left_eye_baseline = left_eye_baseline * 0.95
            WHERE student_number = ?
        ''', (student_number,))
        conn.commit()

        # 更新後の基準値を通知
        socketio.emit('eye_openness_alert', {'message': '基準値を5%下げました。'}, room=student_number)
    else:
        socketio.emit('eye_openness_alert', {'message': '基準値の変更はキャンセルされました。'}, room=student_number)


@socketio.on('response_low_eye_openness')
@student_required
def handle_low_eye_openness_response(data):
    attention_id = data['attention_id']
    response = data['response']

    if response == 'no':
        conn = current_app.get_db()
        cursor = conn.cursor()

        # is_correct カラムを FALSE に更新
        cursor.execute('''
            UPDATE attentions
            SET is_correct = FALSE
            WHERE id = ?
        ''', (attention_id,))

        conn.commit()

        print(f"Attention ID {attention_id} marked as incorrect.")
