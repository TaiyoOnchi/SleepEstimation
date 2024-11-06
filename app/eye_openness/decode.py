import base64
import numpy as np
import cv2 as cv

def decode_image(image_data):
    if image_data.startswith("data:image/jpeg;base64,"):
        image_data = image_data.split(",")[1]
    decoded_data = base64.b64decode(image_data)
    np_arr = np.frombuffer(decoded_data, np.uint8)
    return cv.imdecode(np_arr, cv.IMREAD_COLOR)