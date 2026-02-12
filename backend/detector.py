from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt")

def process_video(video_path):
    cap = cv2.VideoCapture(video_path)

    max_people = 0
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        results = model(frame, verbose=False)

        people = 0
        for r in results:
            for c in r.boxes.cls:
                if int(c) == 0:
                    people += 1

        max_people = max(max_people, people)

    cap.release()

    alerts = []
    if max_people >= 5:
        alerts.append("Crowd threshold exceeded")

    return {
        "frames": frame_count,
        "max_people": max_people,
        "alerts": alerts
    }
