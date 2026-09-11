import time
import cv2
from inference_sdk import InferenceHTTPClient
import requests

# --- CONFIGURATION ---
ROBOFLOW_API_KEY = "YOUR_PRIVATE_API_KEY"  # Replace with your private Roboflow API key
MODEL_ID = "realistic/pothole-detection-yolov8-ehkp9-4dry8-1-yolo26n-t1"
VIDEO_PATH = "demo_video.mp4"  # Path to your local test video file
BACKEND_URL = "http://localhost:5000/api/v1/alerts"

CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="MAP3Tmhscfhm01Tpqp0z"
)

def process_edge_stream():
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"[ERROR] Edge client could not open video source: {VIDEO_PATH}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    print(f"[INFO] Edge client initialized. Streaming frames from {VIDEO_PATH}...")

    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Edge sampling rate: evaluate every 5th frame locally
        if frame_idx % 5 == 0:
            timestamp_sec = round(frame_idx / fps, 2)
            try:
                result = CLIENT.infer(frame, model_id=MODEL_ID)
                predictions = result.get("predictions", [])

                for pred in predictions:
                    class_name = pred.get("class", "").lower()
                    confidence = pred.get("confidence", 0.0)

                    if ("pothole" in class_name or "pot" in class_name or "damage" in class_name) and confidence > 0.35:
                        print(f"[EDGE DETECT] Pothole found at {timestamp_sec}s | Confidence: {confidence:.2f}")

                        payload = {
                            "anomaly_type": "pothole",
                            "confidence": float(confidence),
                            "timestamp_sec": float(timestamp_sec),
                            "route_tag": "Vehicle Node #04 - MG Road",
                            "distance_km": round(timestamp_sec * 0.01, 2),
                            "frame_id": int(frame_idx)
                        }

                        response = requests.post(BACKEND_URL, json=payload)
                        if response.status_code == 200:
                            print("[TELEMETRY] Alert successfully pushed to server.")
                        else:
                            print(f"[TELEMETRY ERROR] Server rejected payload: {response.text}")

            except Exception as e:
                print(f"[EDGE ERROR] Frame {frame_idx} processing failed: {e}")

        frame_idx += 1

    cap.release()
    print("[INFO] Edge processing stream completed.")

if __name__ == "__main__":
    process_edge_stream()