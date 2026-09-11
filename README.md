# vektor
SIH Internal Hackathon 
# Vektor UrbanEye 🚦👁️
Autonomous Edge-to-Cloud Road Anomaly Detection & Telemetry Pipeline

Vektor UrbanEye is a strictly software-based architecture designed for municipal road auditing and automated hazard detection. The system decouples local edge inference from central server-side ingestion, simulating an onboard vehicle client that detects road anomalies in real time and streams telemetry data back to a central municipal command center dashboard.

---

## Architecture Overview
* **Edge Node (`edge_processor.py`):** Acts as the onboard vehicle software client. It samples local video feeds frame-by-frame, performs computer vision inference via the Roboflow Cloud API locally, and pushes JSON telemetry payloads.
* **Backend Server (`app.py`):** A Flask-powered REST API and web dashboard that receives incoming telemetry, stores records in a lightweight SQLite database, and provides live analytics, log management, and CSV report exports.

---

## Prerequisites & Tech Stack
* **Python 3.8+**
* **Dependencies:** Install the required libraries via terminal:
  ```bash
  pip install flask opencv-python requests inference-sdk
