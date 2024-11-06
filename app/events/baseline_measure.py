from flask import session, url_for
from app import socketio
from app.eye_openness import decode_image, process_image, save_baseline_to_database


@socketio.on('measure_baseline')
def measure_baseline_eye_openness(data):
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

    if max_sum_openness and max_sum_openness['eye_right'] >= 0.2 and max_sum_openness['eye_left'] >= 0.2:
        save_baseline_to_database(best_frame, max_sum_openness, student_info)
        socketio.emit('measurement_complete', {'message': '新規登録されました。ログイン画面からログインしてください', 'redirect_url': url_for('app.student.login.login')})
    else:
        message = '目の開眼率が低すぎるため、再測定します' if max_sum_openness else '有効な開眼率が検出されませんでした。再測定します'
        socketio.emit('measurement_complete', {'message': message, 'redirect_url': url_for('app.student.measure_baseline.measure_baseline')})
