import csv
import io
import os
import sqlite3
from flask import Flask, Response, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)
DB_FILE = "urbaneye_demo.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anomaly_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            timestamp_sec REAL NOT NULL,
            route_tag TEXT NOT NULL,
            distance_km REAL NOT NULL,
            frame_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route("/")
def index():
    dashboard_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vektor UrbanEye - Edge Telemetry Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-900 text-gray-100 font-sans">
        <div class="container mx-auto px-4 py-8">
            <header class="flex justify-between items-center mb-8 border-b border-gray-800 pb-4">
                <div>
                    <h1 class="text-3xl font-bold text-red-500">Vektor UrbanEye</h1>
                    <p class="text-sm text-gray-400">Edge-to-Cloud Road Anomaly Telemetry Portal</p>
                </div>
                <div class="space-x-2">
                    <a href="/clear" class="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg font-semibold transition inline-block">Clear Logs</a>
                    <a href="/api/v1/export" class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-semibold transition inline-block">Download CSV</a>
                    <button onclick="fetchAlerts()" class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-semibold transition">Refresh</button>
                </div>
            </header>

            <div class="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-lg mb-8">
                <h2 class="text-lg font-semibold mb-2 text-blue-400">Edge Client Status</h2>
                <p class="text-sm text-gray-300">Run your local <code class="bg-gray-900 px-2 py-1 rounded text-green-400">edge_processor.py</code> script to stream live anomaly frames into this central dashboard.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-lg">
                    <h3 class="text-gray-400 text-sm font-medium">Total Detections</h3>
                    <p id="total-count" class="text-4xl font-black text-white mt-2">0</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-lg">
                    <h3 class="text-gray-400 text-sm font-medium">System Telemetry</h3>
                    <p class="text-4xl font-black text-green-400 mt-2">Connected</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-lg">
                    <h3 class="text-gray-400 text-sm font-medium">Architecture Mode</h3>
                    <p class="text-xl font-bold text-blue-400 mt-3 truncate">Decoupled Edge Node</p>
                </div>
            </div>

            <div class="bg-gray-800 rounded-xl border border-gray-700 shadow-lg overflow-hidden">
                <div class="px-6 py-4 border-b border-gray-700">
                    <h2 class="text-lg font-semibold">Incoming Edge Telemetry Logs</h2>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-gray-700 text-gray-300 text-xs uppercase tracking-wider">
                                <th class="px-6 py-3">ID</th>
                                <th class="px-6 py-3">Type</th>
                                <th class="px-6 py-3">Confidence</th>
                                <th class="px-6 py-3">Timestamp (s)</th>
                                <th class="px-6 py-3">Route Tag</th>
                                <th class="px-6 py-3">Frame ID</th>
                                <th class="px-6 py-3">Logged At</th>
                            </tr>
                        </thead>
                        <tbody id="alerts-table" class="divide-y divide-gray-700 text-sm">
                            <tr>
                                <td colspan="7" class="px-6 py-4 text-center text-gray-500">Waiting for edge telemetry stream...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            async function fetchAlerts() {
                try {
                    const response = await fetch('/api/v1/alerts');
                    const result = await response.json();
                    if (result.status === 'success') {
                        document.getElementById('total-count').innerText = result.count;
                        const tbody = document.getElementById('alerts-table');
                        tbody.innerHTML = '';
                        if (result.data.length === 0) {
                            tbody.innerHTML = `<tr><td colspan="7" class="px-6 py-4 text-center text-gray-500">No edge telemetry recorded yet. Start your edge processor script!</td></tr>`;
                            return;
                        }
                        result.data.forEach(alert => {
                            const row = `
                                <tr class="hover:bg-gray-750 transition">
                                    <td class="px-6 py-4 font-mono">#${alert.id}</td>
                                    <td class="px-6 py-4"><span class="bg-red-900 text-red-200 text-xs px-2.5 py-1 rounded-full uppercase font-bold">${alert.anomaly_type}</span></td>
                                    <td class="px-6 py-4 font-semibold text-green-400">${(alert.confidence * 100).toFixed(1)}%</td>
                                    <td class="px-6 py-4">${alert.timestamp_sec}s</td>
                                    <td class="px-6 py-4">${alert.route_tag}</td>
                                    <td class="px-6 py-4">${alert.frame_id}</td>
                                    <td class="px-6 py-4 text-gray-400 text-xs">${alert.created_at}</td>
                                </tr>
                            `;
                            tbody.innerHTML += row;
                        });
                    }
                } catch (err) {
                    console.error("Failed to load alerts:", err);
                }
            }

            fetchAlerts();
            setInterval(fetchAlerts, 3000);
        </script>
    </body>
    </html>
    """
    return render_template_string(dashboard_html)

@app.route("/clear", methods=["GET"])
def clear_route():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    init_db()
    return redirect(url_for('index'))

@app.route("/api/v1/alerts", methods=["POST"])
def receive_alert():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No JSON payload"}), 400
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO anomalies (anomaly_type, confidence, timestamp_sec, route_tag, distance_km, frame_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get("anomaly_type", "pothole"),
            data.get("confidence", 0.0),
            data.get("timestamp_sec", 0.0),
            data.get("route_tag", "Edge Node Sector A"),
            data.get("distance_km", 0.0),
            data.get("frame_id", 0)
        ))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Telemetry logged"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/v1/alerts", methods=["GET"])
def get_alerts():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM anomalies ORDER BY created_at DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    alerts_list = [dict(row) for row in rows]
    return jsonify({"status": "success", "count": len(alerts_list), "data": alerts_list}), 200

@app.route("/api/v1/export", methods=["GET"])
def export_csv():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, anomaly_type, confidence, timestamp_sec, route_tag, distance_km, frame_id, created_at FROM anomalies ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Anomaly Type", "Confidence", "Timestamp (s)", "Route Tag", "Distance (km)", "Frame ID", "Logged At"])
    writer.writerows(rows)

    response = Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=urbaneye_edge_telemetry.csv"}
    )
    return response

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)