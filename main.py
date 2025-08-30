import os
import pickle
import numpy as np
import cv2
import dlib
from scipy.spatial import distance as dist
import face_recognition
from collections import deque
from mysql.connector import connect, Error
from FingerMatters import FingerMatters  # Import the class

with open("EncodeGenerator.py") as f:
    exec(f.read())

# Database Configuration
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'Vaibhav@2504',
    'database': 'newdata',
}

from datetime import datetime

def mark_attendance(student_id):
    try:
        with connect(**db_config) as connection:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE Students
                SET total_attendance = total_attendance + 1,
                    last_attendance_time = NOW()
                WHERE id = %s
            """, (student_id,))
            connection.commit()
            print(f"Attendance marked for ID: {student_id}")
    except Error as e:
        print(f"Error updating attendance: {e}")


# Constants
EAR_THRESHOLD = 0.26  # Lowered for more sensitivity
CONSEC_FRAMES = 1  # Reduced for faster detection
FRAME_BUFFER_SIZE = 4
MIN_EAR_CHANGE = 0.08  # Adjusted for quicker detection
STABILITY_THRESHOLD = 20  # Further relaxed for less stability checks
LEFT_EYE_IDX = range(42, 48)
RIGHT_EYE_IDX = range(36, 42)

def load_encodings(file_path):
    print("Loading Encode File ...")
    with open(file_path, 'rb') as file:
        encode_list_known_with_ids = pickle.load(file)
    print("Encode File Loaded")
    return encode_list_known_with_ids

def calculate_EAR(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def initialize_dlib():
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    return detector, predictor

def initialize_camera(width=640, height=480):
    cap = cv2.VideoCapture(0)
    cap.set(3, width)
    cap.set(4, height)
    return cap

def get_student_details(student_id):
    try:
        with connect(**db_config) as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, name FROM Students WHERE id = %s", (student_id,))
            return cursor.fetchone()
    except Error as e:
        print(f"Database Error: {e}")
        return None

def is_face_stable(face, face_position_buffer):
    """Check if the face bounding box is stable across frames."""
    x, y, w, h = face.left(), face.top(), face.width(), face.height()
    face_position_buffer.append((x, y, w, h))
    if len(face_position_buffer) < FRAME_BUFFER_SIZE:
        return True  # Not enough data yet

    # Calculate movement
    deltas = [np.linalg.norm(np.array(face_position_buffer[i]) - np.array(face_position_buffer[i - 1]))
              for i in range(1, len(face_position_buffer))]
    return max(deltas) < STABILITY_THRESHOLD

def enhanced_blink_detection(avg_ear, blink_counter, consecutive_blinks, ear_buffer):
    """Enhanced blink detection with stability checks."""
    ear_buffer.append(avg_ear)
    if len(ear_buffer) < FRAME_BUFFER_SIZE:
        return blink_counter, consecutive_blinks  # Not enough data yet

    # Check EAR change
    ear_drop = ear_buffer[-1] < EAR_THRESHOLD and (ear_buffer[0] - ear_buffer[-1]) > MIN_EAR_CHANGE
    if ear_drop:
        blink_counter += 1
    else:
        if blink_counter >= CONSEC_FRAMES:
            consecutive_blinks += 1
            print(f"Blink {consecutive_blinks} confirmed!")
        blink_counter = 0

    return blink_counter, consecutive_blinks

def process_face_recognition(frame, face, encode_list_known, student_ids):
    face_img = frame[max(0, face.top()):min(face.bottom(), frame.shape[0]),
               max(0, face.left()):min(face.right(), frame.shape[1])]
    face_img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
    encode_cur_frame = face_recognition.face_encodings(face_img_rgb)

    if encode_cur_frame:
        encode_face = encode_cur_frame[0]
        matches = face_recognition.compare_faces(encode_list_known, encode_face)
        face_dis = face_recognition.face_distance(encode_list_known, encode_face)
        match_index = np.argmin(face_dis)

        if matches[match_index]:
            student_id = student_ids[match_index]
            student = get_student_details(student_id)
            if student:
                print(f"Liveness confirmed: {student['id']} - {student['name']}")
                return student
    return None

def main():
    encode_list_known, student_ids = load_encodings('EncodeFile.p')
    detector, predictor = initialize_dlib()
    cap = initialize_camera()

    blink_counter = 0
    consecutive_blinks = 0
    process_live_face = False
    ear_buffer = deque(maxlen=FRAME_BUFFER_SIZE)
    face_position_buffer = deque(maxlen=FRAME_BUFFER_SIZE)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Camera not capturing frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        for face in faces:
            # Ensure face is stable
            if not is_face_stable(face, face_position_buffer):
                continue

            landmarks = predictor(gray, face)
            landmarks_points = np.array([[p.x, p.y] for p in landmarks.parts()])

            left_eye = landmarks_points[LEFT_EYE_IDX]
            right_eye = landmarks_points[RIGHT_EYE_IDX]

            left_ear = calculate_EAR(left_eye)
            right_ear = calculate_EAR(right_eye)
            avg_ear = (left_ear + right_ear) / 2.0

            blink_counter, consecutive_blinks = enhanced_blink_detection(avg_ear, blink_counter, consecutive_blinks,
                                                                         ear_buffer)

            if consecutive_blinks == 2:
                process_live_face = True

            if process_live_face:
                student = process_face_recognition(frame, face, encode_list_known, student_ids)
                if student:
                    cv2.putText(frame, f"{student['name']} ({student['id']})", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    mark_attendance(student['id'])
                    consecutive_blinks = 0
                    process_live_face = False
                else:
                    cap.release()
                    cv2.destroyAllWindows()
                    app = FingerMatters()
                    app.detect_fingers()


        cv2.imshow("Live Face Detection", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
