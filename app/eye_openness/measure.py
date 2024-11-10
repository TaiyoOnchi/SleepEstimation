import cv2 as cv
import numpy as np
import mediapipe as mp
import math

# MediapipeのFaceMeshモジュールを初期化
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5, refine_landmarks=True
)

# 目のランドマークインデックス
landmark_index_dict = {'eye_right': [133, 33, 159, 145], 'eye_left': [362, 263, 386, 374]}

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
        
        # ピッチ角（顔の傾き）を計算(正面が90°)
        pitch_angle = calculate_pitch_angle(landmarks, frame)
        print(pitch_angle)


        # 目の開眼率を計算
        eye_openness = calculate_eye_openness(landmarks, frame)

        # 各目（'eye_right' と 'eye_left'）に対して、ピッチ角を考慮した補正を適用
        corrected_eye_openness = {
            
            # 'eye_right' と 'eye_left' に対応する開眼率（openness）を apply_pitch_correction 関数で補正
            eye: apply_pitch_correction(openness, pitch_angle) 
            
            # eye_openness.items() → 目の開眼率が格納されている辞書からキー（'eye_right'、'eye_left'）と値（目の開眼率）を取得
            for eye, openness in eye_openness.items()  # eye → 'eye_right' , 'eye_left'、openness → 開眼率(0.2など)
        }



        return frame, corrected_eye_openness
    else:
        # 顔が検出されなかった場合
        return frame, None

# ピッチ角を計算する関数
def calculate_pitch_angle(landmarks, img):
    # 顎の先端と鼻の先端の座標を取得（ピッチ角計算のため）
    nose_tip = np.array([landmarks[1].x * img.shape[1], landmarks[1].y * img.shape[0]])
    chin = np.array([landmarks[152].x * img.shape[1], landmarks[152].y * img.shape[0]])

    # 鼻と顎の高さの差と横の差を計算
    y_diff = chin[1] - nose_tip[1]
    x_diff = chin[0] - nose_tip[0]
    # 角度（ラジアン）を求め、度に変換
    pitch_angle = math.degrees(math.atan2(y_diff, x_diff))
    return pitch_angle


def calculate_eye_openness(landmarks, img):
    # 左右の目の内側のランドマークを取得して距離を計算
    eye_inner_left = np.array([landmarks[133].x * img.shape[1], landmarks[133].y * img.shape[0]])
    eye_inner_right = np.array([landmarks[362].x * img.shape[1], landmarks[362].y * img.shape[0]])
    eye_distance = np.linalg.norm(eye_inner_left - eye_inner_right)

    # 各目のランドマーク位置を取得
    landmark_dict = {'eye_right': [], 'eye_left': []}
    for eye in landmark_index_dict:
        for i in landmark_index_dict[eye]:
            res_x = int(landmarks[i].x * img.shape[1])
            res_y = int(landmarks[i].y * img.shape[0])
            landmark_dict[eye].append((res_x, res_y))

    eye_openness_dict = {}
    # 右目と左目の開眼率をそれぞれ計算
    for eye in ['eye_right', 'eye_left']:
        eye_head = landmark_dict[eye][0]
        eye_tail = landmark_dict[eye][1]
        total_eye_openness = 0
        # まぶたの上と下のランドマークで開眼度を測定
        for lid_index in [2, 3]:
            lid_point = landmark_dict[eye][lid_index]
            perpendicular_point = calculate_perpendicular_point(eye_head, eye_tail, lid_point)
            distance = np.linalg.norm(np.array(lid_point) - perpendicular_point)
            total_eye_openness += distance
        # 「目の間の距離」を基準に開眼率を正規化
        eye_openness_dict[eye] = total_eye_openness / eye_distance

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

# ピッチ角に基づいて目の開眼率を補正する関数
# ピッチ角に基づいて目の開眼率を補正する関数
def apply_pitch_correction(eye_openness, pitch_angle):
    # ピッチ角が前傾している場合、開眼率を調整（角度が大きいほど補正）
    n=50
    correction_factor = 1 + abs(abs(pitch_angle)-90) / n  # 上を向くと90↓、下を向くと90↑(補正変更可)
    # 開眼率を補正した値で返す
    corrected_eye_openness = eye_openness * correction_factor
    print(corrected_eye_openness ,eye_openness ,correction_factor)
    return corrected_eye_openness

