import cv2 as cv
import numpy as np
import mediapipe as mp

# MediapipeのFaceMeshモジュールを初期化
mp_face_mesh = mp.solutions.face_mesh
# FaceMeshオブジェクトを設定。静止画像モードをオフ、最大1人の顔を認識、信頼度0.5以上で検出
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5, refine_landmarks=True
)

# 目のランドマークインデックスの辞書
landmark_index_dict = {'eye_right': [133, 33, 159, 145], 'eye_left': [362, 263, 386, 374]}

# 開眼率測定機能関数
def process_image(frame):
    # 画像をRGBに変換
    img_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    # 顔ランドマークを検出
    results = face_mesh.process(img_rgb)

    # 顔ランドマークが検出された場合
    if results.multi_face_landmarks:
        # ランドマークを取得し、鼻の先端と上唇の位置を計算
        landmarks = results.multi_face_landmarks[0].landmark
        nose_tip = np.array([landmarks[1].x * frame.shape[1], landmarks[1].y * frame.shape[0]])
        upper_lip = np.array([landmarks[13].x * frame.shape[1], landmarks[13].y * frame.shape[0]])
        # 鼻と唇の距離を計算
        nose_to_lip_distance = np.linalg.norm(nose_tip - upper_lip)
        # 開眼率を計算
        eye_openness = calculate_eye_openness(landmarks, frame, nose_to_lip_distance)
        return frame, eye_openness
    else:
        return frame, None

# 開眼率を計算する関数
def calculate_eye_openness(landmarks, img, nose_to_lip_distance):
    landmark_dict = {'eye_right': [], 'eye_left': []}
    # 各目のランドマーク位置を取得
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
            # まぶたの点と垂直距離を計算し、開眼度に加算
            distance = np.linalg.norm(np.array(lid_point) - perpendicular_point)
            total_eye_openness += distance
        # 鼻と唇の距離で開眼度を正規化
        eye_openness_dict[eye] = total_eye_openness / nose_to_lip_distance

    return eye_openness_dict

# 垂線の点を計算する関数
def calculate_perpendicular_point(eye_head, eye_tail, lid_point):
    # 目の直線のベクトルを計算
    eye_line_vector = np.array(eye_tail) - np.array(eye_head)
    eye_line_length = np.linalg.norm(eye_line_vector)
    eye_line_unit_vector = eye_line_vector / eye_line_length
    # まぶたの点から直線への垂線の投影長を計算
    head_to_lid_vector = np.array(lid_point) - np.array(eye_head)
    projection_length = np.dot(head_to_lid_vector, eye_line_unit_vector)
    # 目の直線上の垂線の点を計算
    perpendicular_point = np.array(eye_head) + projection_length * eye_line_unit_vector
    return perpendicular_point
