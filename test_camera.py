import cv2

cap = cv2.VideoCapture('v4l2:///dev/video0', cv2.CAP_GSTREAMER)
if cap.isOpened():
    print("✅ Camera opened successfully!")
else:
    print("❌ Failed to open camera.")
cap.release()
