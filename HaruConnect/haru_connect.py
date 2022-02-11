import cv2
import dlib
import numpy as np
import socket


face_detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')


# 偵測單一人臉的臉部特徵(假設圖像中只有一個人)
def get_face_shape(image):
    image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    shapes = face_detector(image, 0)

    if not shapes:
        return None

    shape = max(shapes, key=lambda shape: (shape.right() - shape.left()) * (shape.bottom() - shape.top()))
    
    return shape


# 將dlib偵測到的人臉68個特徵點取出
def get_face_68_landmarks(shape, dtype="int"):
    shape = shape_predictor(image, shape)
    marks = np.zeros((68, 2), dtype=dtype)

    for i in range(0, 68):
        marks[i] = (shape.part(i).x, shape.part(i).y)
 
    return marks


# 取得左右眼睛、左右眉毛、嘴巴的特徵點區塊
def get_face_motion_landmarks(marks):
    left_eye = marks[36:42]
    right_eye = marks[42:48]
    left_eyebrow = marks[17:22]
    right_eyebrow = marks[22:27]
    mouth = marks[60:68]

    return left_eye, right_eye, left_eyebrow, right_eyebrow, mouth


# 取得人臉向量
def get_face_vectors(marks, image):
    image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    # 鼻尖 Nose tip: 34
    nose_tip = marks[33:34]
    # 下巴 Chin: 9
    chin = marks[8:9]
    # 左眼左角 Left eye left corner: 37
    left_eye_corner = marks[36:37]
    # 右眼右角 Right eye right corner: 46
    right_eye_corner = marks[45:46]
    # 嘴巴左角 Left Mouth corner: 49
    left_mouth_corner = marks[48:49]
    # 嘴巴右角 Right Mouth corner: 55
    right_mouth_corner = marks[54:55]

    # 把相關的6個座標串接起來
    face_points = np.concatenate((nose_tip, chin, left_eye_corner, right_eye_corner, left_mouth_corner, right_mouth_corner))
    face_points = face_points.astype(np.double)

    # 3維模型的座標點 (使用一般的3D人臉模型的座標點)
    model_points = np.array([
                                (0.0, 0.0, 0.0),             # Nose tip
                                (0.0, -330.0, -65.0),        # Chin
                                (-225.0, 170.0, -135.0),     # Left eye left corner
                                (225.0, 170.0, -135.0),      # Right eye right corne
                                (-150.0, -150.0, -125.0),    # Left Mouth corner
                                (150.0, -150.0, -125.0)      # Right mouth corner                         
                            ])

    size = image.shape
    # 焦距
    focal_length = size[1] 
    # 照像機內部成像的中心點(w, h)
    center = (size[1]/2, size[0]/2)
    # 照像機參數 (Camera internals )
    camera_matrix = np.array(
                            [[focal_length, 0, center[0]],
                            [0, focal_length, center[1]],
                            [0, 0, 1]], dtype = "double"
                            )
    # 扭曲係數
    dist_coeffs = np.zeros((4,1)) # 假設沒有鏡頭的成像扭曲 (no lens distortion)

    # 使用OpenCV的solvePnP函數來計算人臉的旋轉與位移
    (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points, face_points, camera_matrix , dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)
    
    return rotation_vector, translation_vector


# 計算歐拉角,[pitch]頭抬低、[yaw]頭左右轉、[roll]頭左右傾
def calculate_euler_angles(rotation_vector, translation_vector):
    rvec_matrix = cv2.Rodrigues(rotation_vector)[0]
    proj_matrix = np.hstack((rvec_matrix, translation_vector))
    eulerAngles = -cv2.decomposeProjectionMatrix(proj_matrix)[6]

    pitch = eulerAngles[0]
    yaw   = eulerAngles[1]
    roll  = eulerAngles[2]

    if pitch > 0:
        pitch = 180 - pitch

    elif pitch < 0:
        pitch = -180 - pitch

    pitch = -pitch + 8
    roll = -roll

    return pitch, yaw, roll


# 取得凝視追蹤座標與距離
def get_gaze_tracing(image, marks):
    mask = np.full(image.shape[:2], 255, np.uint8)
    region = marks.astype(np.int32)

    try:
        cv2.fillPoly(mask, [region], (0, 0, 0))
        eye = cv2.bitwise_not(image, image.copy(), mask=mask)

        margin = 4
        min_x = np.min(region[:, 0]) - margin
        max_x = np.max(region[:, 0]) + margin
        min_y = np.min(region[:, 1]) - margin
        max_y = np.max(region[:, 1]) + margin

        eye = eye[min_y:max_y, min_x:max_x]
        eye = cv2.cvtColor(eye, cv2.COLOR_RGB2GRAY)
        eye_binarized = cv2.threshold(eye, np.quantile(eye, 0.2), 255, cv2.THRESH_BINARY)[1]
        contours, _ = cv2.findContours(eye_binarized, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea)
        moments = cv2.moments(contours[-2])

        x = int(moments['m10'] / moments['m00']) + min_x
        y = int(moments['m01'] / moments['m00']) + min_y

        return x, y, (x-min_x-margin)/(max_x-min_x-2*margin), (y-min_y-margin)/(max_y-min_y-2*margin)

    except:
        return 0, 0, 0.5, 0.5


#取得眼睛縱橫比
def get_eye_aspect_ratio(eye):
    ear = np.linalg.norm(eye[1]-eye[5]) + np.linalg.norm(eye[2]-eye[4])
    ear/= (2*np.linalg.norm(eye[0]-eye[3])+1e-6)

    return ear


#取得嘴巴縱橫比
def get_mouth_aspect_ratio(mouth):
    mar = np.linalg.norm(mouth[1]-mouth[7]) + np.linalg.norm(mouth[2]-mouth[6]) + np.linalg.norm(mouth[3]-mouth[5])
    mar/= (2*np.linalg.norm(mouth[0]-mouth[4])+1e-6)

    return mar


# 與 Unity 連線
def connect_unity(pitch, yaw, roll, min_ear, mar):
    address = ('127.0.0.1', 1234)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(address)

    message = '%.5f %.5f %.5f %.5f %.5f' % (pitch, yaw, roll, min_ear, mar)
    s.send(bytes(message, "utf-8"))


# 主程式
cap = cv2.VideoCapture(0)

while True:
    hx, image = cap.read()

    if hx is False:
        print('read video error')
        exit()
    
    image = cv2.flip(image, 1)
    face_shape = get_face_shape(image)

    if face_shape is not None:
        face_68_landmarks = get_face_68_landmarks(face_shape)

        # for i, (px, py) in enumerate(face_68_landmarks):
            # cv2.putText(image, str(i), (int(px),int(py)), cv2.FONT_HERSHEY_COMPLEX, 0.25, (0, 0, 0))

        left_eye, right_eye, left_eyebrow, right_eyebrow, mouth = get_face_motion_landmarks(face_68_landmarks)

        rotation_vector, translation_vector = get_face_vectors(face_68_landmarks, image)

        pitch, yaw, roll = calculate_euler_angles(rotation_vector, translation_vector)

        left_x, left_y, left_x_ratio, left_y_ratio = get_gaze_tracing(image, left_eye)
        right_x, right_y, right_x_ratio, right_y_ratio = get_gaze_tracing(image, right_eye)

        left_ear = get_eye_aspect_ratio(left_eye)
        right_ear = get_eye_aspect_ratio(right_eye)

        mar = get_mouth_aspect_ratio(mouth)

        left_gaze = (left_x, left_y)
        right_gaze = (right_x, right_y)

        min_ear = min(left_ear, right_ear)

        # cv2.putText(image, "[min_ear]" + str(min_ear), (0, 80), cv2.FONT_HERSHEY_TRIPLEX, 1.5, (0, 255, 0), 1, cv2.LINE_AA)
        # cv2.putText(image, "[mar]" + str(mar), (0, 120), cv2.FONT_HERSHEY_TRIPLEX, 1.5, (0, 255, 0), 1, cv2.LINE_AA)
        # cv2.putText(image, "[pitch]" + str(pitch), (0, 160), cv2.FONT_HERSHEY_TRIPLEX, 1.5, (0, 255, 0), 1, cv2.LINE_AA)
        # cv2.putText(image, "[yaw]" + str(yaw), (0, 200), cv2.FONT_HERSHEY_TRIPLEX, 1.5, (0, 255, 0), 1, cv2.LINE_AA)
        # cv2.putText(image, "[roll]" + str(roll), (0, 240), cv2.FONT_HERSHEY_TRIPLEX, 1.5, (0, 255, 0), 1, cv2.LINE_AA)


        connect_unity(pitch, yaw, roll, min_ear, mar)
    
    cv2.imshow('video', image)
    if cv2.waitKey(1) & 0xFF == ord('p'):
        break

cap.release()
cv2.destroyAllWindows()