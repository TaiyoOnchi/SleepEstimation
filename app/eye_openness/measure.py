import cv2 as cv
import numpy as np
import mediapipe as mp
import math

# MediapipeのFaceMeshモジュールを初期化
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5, refine_landmarks=True
)



# 画像を処理し、目の開眼率を計算する関数
def process_image(frame):
    # 画像をBGRからRGBに変換（MediapipeはRGB形式を必要とする）
    img_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    # MediapipeのFaceMeshを使って顔のランドマークを検出
    results = face_mesh.process(img_rgb)

    # 顔が検出されている場合
    if results.multi_face_landmarks:
        # 顔のランドマークを取得
        landmarks = results.multi_face_landmarks[0].landmark
        
        # 目の開眼率を計算
        eye_openness = calculate_eye_openness(landmarks, frame)

        # # 各目（'eye_right' と 'eye_left'）に対して、ピッチ角を考慮した補正を適用
        # corrected_eye_openness = {
            
        #     # 'eye_right' と 'eye_left' に対応する開眼率（openness）を apply_pitch_correction 関数で補正
        #     eye: apply_pitch_correction(openness, pitch_angle) 
            
        #     # eye_openness.items() → 目の開眼率が格納されている辞書からキー（'eye_right'、'eye_left'）と値（目の開眼率）を取得
        #     for eye, openness in eye_openness.items()  # eye → 'eye_right' , 'eye_left'、openness → 開眼率(0.2など)
        # }

        return frame, eye_openness
    else:
        # 顔が検出されなかった場合
        return frame, None





def calculate_nose_length(landmarks, img):
    #ランドマーク4と197の距離を計算して鼻の長さを取得する。
    nose_start = np.array([landmarks[4].x * img.shape[1], landmarks[4].y * img.shape[0]])
    nose_end = np.array([landmarks[197].x * img.shape[1], landmarks[197].y * img.shape[0]])
    nose_length = np.linalg.norm(nose_end - nose_start)
    print(nose_length)
    return nose_length

def calculate_eye_openness(landmarks, img):
    # 結果を格納する辞書
    eye_openness_dict = {}

    # 鼻の長さを計算
    nose_length = calculate_nose_length(landmarks, img)

    # 左目と右目それぞれに対して計算
    for eye in ['eye_right', 'eye_left']:
        # 目頭と目じりのランドマークインデックス
        if eye == 'eye_right':
            head_idx, tail_idx = 263, 362  # 右目の目頭と目じり
            upper_indices = [398, 384, 385, 386, 387, 388, 466]  # 上のランドマーク候補
            lower_indices = [249, 390, 373, 374, 380, 381, 382]  # 下のランドマーク候補
        else:
            head_idx, tail_idx = 33, 133  # 左目の目頭と目じり
            upper_indices = [173, 157, 158, 159, 160, 161, 246]  # 上のランドマーク候補
            lower_indices = [7, 163, 144, 145, 153, 154, 155]  # 下のランドマーク候補

        # 目頭と目じりの座標を取得
        eye_head = np.array([landmarks[head_idx].x * img.shape[1], landmarks[head_idx].y * img.shape[0]])
        eye_tail = np.array([landmarks[tail_idx].x * img.shape[1], landmarks[tail_idx].y * img.shape[0]])

        # 上まぶた・下まぶたの最大距離を初期化
        max_upper_distance = 0
        max_lower_distance = 0

        # 上まぶたのランドマークを処理
        for idx in upper_indices:
            lid_point = np.array([landmarks[idx].x * img.shape[1], landmarks[idx].y * img.shape[0]])
            perpendicular_point = calculate_perpendicular_point(eye_head, eye_tail, lid_point)
            distance = np.linalg.norm(lid_point - perpendicular_point)
            max_upper_distance = max(max_upper_distance, distance)

        # 下まぶたのランドマークを処理
        for idx in lower_indices:
            lid_point = np.array([landmarks[idx].x * img.shape[1], landmarks[idx].y * img.shape[0]])
            perpendicular_point = calculate_perpendicular_point(eye_head, eye_tail, lid_point)
            distance = np.linalg.norm(lid_point - perpendicular_point)
            max_lower_distance = max(max_lower_distance, distance)

        # 開眼度を計算（上まぶたと下まぶたの最大距離の和）
        total_eye_openness = max_upper_distance + max_lower_distance

        # 鼻の長さで正規化
        if nose_length > 0:
            eye_openness_dict[eye] = total_eye_openness / nose_length
        else:
            eye_openness_dict[eye] = 0  # 鼻の長さが計算できない場合に備えた安全処理

    return eye_openness_dict



# 垂直投影点を計算する関数
def calculate_perpendicular_point(eye_head, eye_tail, lid_point):
    # 目の直線のベクトルを計算
    eye_line_vector = np.array(eye_tail) - np.array(eye_head)
    eye_line_length = np.linalg.norm(eye_line_vector)
    # 目の直線ベクトルの単位ベクトルを計算
    eye_line_unit_vector = eye_line_vector / eye_line_length
    # まぶたの点から目の直線への垂直投影を計算
    head_to_lid_vector = np.array(lid_point) - np.array(eye_head)
    projection_length = np.dot(head_to_lid_vector, eye_line_unit_vector)
    # 垂直投影した点を計算
    perpendicular_point = np.array(eye_head) + projection_length * eye_line_unit_vector
    return perpendicular_point


# def calculate_pitch_angle(landmarks, img):
#     # 顎の先端と鼻の先端の座標を取得（3D座標を使用）
#     nose_tip = np.array([landmarks[1].x, landmarks[1].y, landmarks[1].z])
#     chin = np.array([landmarks[152].x, landmarks[152].y, landmarks[152].z])

#     # z方向も含めた高さ差（yとzの変化量のみを考慮）
#     y_diff = chin[1] - nose_tip[1]
#     z_diff = chin[2] - nose_tip[2]

#     # ピッチ角を計算（ラジアンから度へ変換）
#     pitch_angle = math.degrees(math.atan2(z_diff, y_diff))
#     return pitch_angle



# # ピッチ角に基づいて目の開眼率を補正する関数
# def apply_pitch_correction(eye_openness, pitch_angle):
#     # ピッチ角が前傾している場合、開眼率を調整（角度が大きいほど補正）
#     n=50
#     correction_factor = 1 + abs(abs(pitch_angle)-90) / n  # 上を向くと90↓、下を向くと90↑(補正変更可)
#     # 開眼率を補正した値で返す
#     corrected_eye_openness = eye_openness * correction_factor
#     print(corrected_eye_openness ,eye_openness ,correction_factor)
#     return corrected_eye_openness