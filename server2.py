from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file
import os
import json
import io         
import re          
from datetime import datetime

from processData import process_and_store_log, get_all_analytics, get_user_analytics, get_all_users
from db_handler import (
    get_all_users_db, get_user_details, get_user_devices, 
    get_device_details, get_usage_analytics, get_resource_alerts
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Directories
LOG_DIR = "user_logs"
DATA_DIR = "processed_data"
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ==================== LOG RECEIVER ====================
@app.route('/admin', methods=['POST'])
@app.route('/admin/', methods=['POST'])
def receive_log():
    """Receives log data from clients"""
    data = request.get_data(as_text=True)
    client_ip = request.remote_addr

    print("\n" + "="*50)
    print("📥 RECEIVED LOG DATA:")
    print(f"From IP: {client_ip}")
    print(data[:500] + "..." if len(data) > 500 else data)
    print("="*50)

    try:
        result = process_and_store_log(data, client_ip)
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Error processing log: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ==================== ADMIN DASHBOARD ====================
@app.route('/admin/showUsers')
def show_users():
    """Admin dashboard showing all users with cards"""
    users = get_all_users_db()
    analytics = get_usage_analytics()
    alerts = get_resource_alerts()
    return render_template('admin_users.html', users=users, analytics=analytics, alerts=alerts)

@app.route('/admin/user/<int:user_id>')
def user_details_page(user_id):
    """Get detailed user info with assigned devices"""
    user = get_user_details(user_id)
    devices = get_user_devices(user_id)
    return render_template('user_details.html', user=user, devices=devices)

@app.route('/api/user/<int:user_id>')
def api_user_details(user_id):
    """API endpoint for user details"""
    user = get_user_details(user_id)
    devices = get_user_devices(user_id)
    return jsonify({"user": user, "devices": devices})

@app.route('/api/device/<int:device_id>/logs')
def api_device_logs(device_id):
    """API endpoint for device log data from processed files"""
    device = get_device_details(device_id)
    if device and device.get('serial'):
        log_data = get_device_log_data(device['serial'])
        return jsonify({"device": device, "log_data": log_data})
    return jsonify({"error": "Device not found"}), 404

@app.route('/api/analytics')
def api_analytics():
    """API endpoint for analytics data"""
    return jsonify(get_usage_analytics())

@app.route('/api/alerts')
def api_alerts():
    """API endpoint for resource alerts"""
    return jsonify(get_resource_alerts())

# ==================== HELPER FUNCTIONS ====================
def get_device_log_data(serial):
    """Get processed log data for a device by serial"""
    analytics_file = os.path.join(DATA_DIR, "analytics.json")
    if os.path.exists(analytics_file):
        with open(analytics_file, 'r') as f:
            all_data = json.load(f)
            for user_id, data in all_data.items():
                if data.get('hardware', {}).get('serial') == serial:
                    return data
    return None


TEMPLATE_BAT_PATH = "ResourceTracker.bat"  # base BAT in project root

@app.route("/user/setUpUsage", methods=["GET", "POST"])
def user_setup_usage():
    """
    Step 1: ask for username
    Step 2: show directions + download button with personalized BAT
    """
    if request.method == "GET":
        # Just show username form
        return render_template("user_setup.html", step="form", username="")

    # POST – user submitted username
    username = (request.form.get("username") or "").strip()
    if not username:
        return render_template(
            "user_setup.html",
            step="form",
            username="",
            error="Please enter a username."
        )

    # Step 2: show instructions and a download button
    return render_template(
        "user_setup.html",
        step="instructions",
        username=username
    )

@app.route("/user/downloadBat")
def download_bat():
    """
    Generate BAT file with USERNAME=<username> patched in.
    Expects ?username=... (already trimmed).
    """
    username = (request.args.get("username") or "").strip()
    if not username:
        return "Username is required", 400

    if not os.path.exists(TEMPLATE_BAT_PATH):
        return "Base BAT file not found on server", 500

    # Read original BAT template
    with open(TEMPLATE_BAT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace the USERNAME line (assumes exact pattern exists once)
    # Example in BAT:  SET "USERNAME=user001"
    content, count = re.subn(
        r'SET\s+"USERNAME=.*?"',
        f'SET "USERNAME={username}"',
        content,
        count=1,
    )

    # Fallback: if pattern not found, prepend a line
    if count == 0:
        content = f'SET "USERNAME={username}"\n' + content

    # Serve as downloadable file (in‑memory, no temp files)
    file_stream = io.BytesIO(content.encode("utf-8"))
    filename = (f"ResourceTracker_{username}.bat")
    return send_file(
        file_stream,
        as_attachment=True,
        download_name=filename,
        mimetype="application/octet-stream",
    )




if __name__ == '__main__':
    print("🚀 Device Management Server running on http://localhost:8000")
    print("📊 Endpoints:")
    print("   POST /admin - Receive log data")
    print("   GET /admin/showUsers - Admin dashboard")
    print("   GET /admin/user/<id> - User details")
    print("   GET /api/analytics - Analytics data")
    app.run(host='0.0.0.0', port=8000, debug=True)