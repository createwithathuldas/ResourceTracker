import os
import re
import json
import csv
from datetime import datetime

# Directories for storage
LOG_DIR = "user_logs"
DATA_DIR = "processed_data"
ANALYTICS_FILE = os.path.join(DATA_DIR, "analytics.json")

# Ensure directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

def parse_log_data(raw_data):
    """
    Parse the raw log data and extract structured information
    """
    parsed = {
        "timestamp": None,
        "computer_name": None,
        "username": None,
        "gps_location": None,
        "latitude": None,
        "longitude": None,
        "manufacturer": None,
        "model": None,
        "serial": None,
        "cpu_name": None,
        "cpu_cores": None,
        "max_clock_speed": None,
        "total_ram_gb": None,
        "available_ram_mb": None,
        "total_storage_gb": None,
        "available_storage_gb": None
    }

    lines = raw_data.strip().split('\n')

    for line in lines:
        line = line.strip()

        # Extract timestamp and computer name from header
        timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (.+)', line)
        if timestamp_match:
            parsed["timestamp"] = timestamp_match.group(1)
            parsed["computer_name"] = timestamp_match.group(2).strip()
            continue

        # Key-value parsing
        if ':' in line and not line.startswith('='):
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()

            if 'username' in key:
                parsed["username"] = value
            elif 'gps' in key or 'location' in key:
                parsed["gps_location"] = value
                gps_match = re.search(r'([\d.-]+)\s*,\s*([\d.-]+)', value)
                if gps_match:
                    parsed["latitude"] = float(gps_match.group(1))
                    parsed["longitude"] = float(gps_match.group(2))
            elif 'manufacturer' in key:
                parsed["manufacturer"] = value
            elif 'model' in key:
                parsed["model"] = value
            elif 'serial' in key:
                parsed["serial"] = value
            elif 'cpu name' in key:
                parsed["cpu_name"] = value
            elif 'cpu cores' in key or 'cores' in key:
                try:
                    parsed["cpu_cores"] = int(value)
                except:
                    parsed["cpu_cores"] = value
            elif 'clock speed' in key:
                parsed["max_clock_speed"] = value
            elif 'total ram' in key:
                try:
                    parsed["total_ram_gb"] = float(re.search(r'[\d.]+', value).group())
                except:
                    parsed["total_ram_gb"] = value
            elif 'available ram' in key:
                try:
                    parsed["available_ram_mb"] = float(re.search(r'[\d.]+', value).group())
                except:
                    parsed["available_ram_mb"] = value
            elif 'total storage' in key:
                try:
                    parsed["total_storage_gb"] = float(re.search(r'[\d.]+', value).group())
                except:
                    parsed["total_storage_gb"] = value
            elif 'available storage' in key:
                try:
                    parsed["available_storage_gb"] = float(re.search(r'[\d.]+', value).group())
                except:
                    parsed["available_storage_gb"] = value

    return parsed

def get_unique_identifier(parsed_data):
    """
    Generate unique identifier for user based on:
    1. Username (primary)
    2. Serial number (fallback)
    3. Computer name (last resort)
    """
    if parsed_data.get("username"):
        return parsed_data["username"]
    elif parsed_data.get("serial"):
        return f"serial_{parsed_data['serial']}"
    elif parsed_data.get("computer_name"):
        return f"pc_{parsed_data['computer_name']}"
    else:
        return f"unknown_{datetime.now().strftime('%Y%m%d%H%M%S')}"

def process_and_store_log(raw_data, client_ip=None):
    """
    Main function to process incoming log data
    - Parse the data
    - Identify user uniquely
    - Replace existing log file (keep only latest)
    - Store processed data for analytics
    """
    parsed_data = parse_log_data(raw_data)
    parsed_data["client_ip"] = client_ip
    parsed_data["received_at"] = datetime.now().isoformat()

    user_id = get_unique_identifier(parsed_data)
    parsed_data["user_id"] = user_id

    user_log_file = os.path.join(LOG_DIR, f"{user_id}.log")
    user_json_file = os.path.join(DATA_DIR, f"{user_id}.json")

    # REPLACE existing log file with new one (only latest data needed)
    with open(user_log_file, 'w', encoding='utf-8') as f:
        f.write(raw_data)

    with open(user_json_file, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, indent=2)

    update_analytics(user_id, parsed_data)
    update_csv_data(user_id, parsed_data)

    print(f"✅ Processed log for user: {user_id}")
    print(f"   Log file: {user_log_file}")
    print(f"   Data file: {user_json_file}")

    return {
        "status": "success",
        "user_id": user_id,
        "message": f"Log processed and stored for {user_id}"
    }

def update_analytics(user_id, parsed_data):
    """Update the master analytics JSON file"""
    analytics = {}

    if os.path.exists(ANALYTICS_FILE):
        with open(ANALYTICS_FILE, 'r') as f:
            analytics = json.load(f)

    analytics[user_id] = {
        "last_updated": parsed_data.get("received_at"),
        "timestamp": parsed_data.get("timestamp"),
        "computer_name": parsed_data.get("computer_name"),
        "username": parsed_data.get("username"),
        "location": {
            "gps": parsed_data.get("gps_location"),
            "latitude": parsed_data.get("latitude"),
            "longitude": parsed_data.get("longitude")
        },
        "hardware": {
            "manufacturer": parsed_data.get("manufacturer"),
            "model": parsed_data.get("model"),
            "serial": parsed_data.get("serial")
        },
        "cpu": {
            "name": parsed_data.get("cpu_name"),
            "cores": parsed_data.get("cpu_cores"),
            "max_clock_speed": parsed_data.get("max_clock_speed")
        },
        "memory": {
            "total_ram_gb": parsed_data.get("total_ram_gb"),
            "available_ram_mb": parsed_data.get("available_ram_mb")
        },
        "storage": {
            "total_gb": parsed_data.get("total_storage_gb"),
            "available_gb": parsed_data.get("available_storage_gb")
        },
        "client_ip": parsed_data.get("client_ip")
    }

    with open(ANALYTICS_FILE, 'w') as f:
        json.dump(analytics, f, indent=2)

def update_csv_data(user_id, parsed_data):
    """Update CSV file for tabular analytics"""
    csv_file = os.path.join(DATA_DIR, "all_users_data.csv")

    fieldnames = [
        'user_id', 'username', 'computer_name', 'timestamp', 'received_at',
        'client_ip', 'latitude', 'longitude', 'manufacturer', 'model', 
        'serial', 'cpu_name', 'cpu_cores', 'max_clock_speed',
        'total_ram_gb', 'available_ram_mb', 'total_storage_gb', 'available_storage_gb'
    ]

    existing_data = {}
    if os.path.exists(csv_file):
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_data[row['user_id']] = row

    existing_data[user_id] = {
        'user_id': user_id,
        'username': parsed_data.get('username', ''),
        'computer_name': parsed_data.get('computer_name', ''),
        'timestamp': parsed_data.get('timestamp', ''),
        'received_at': parsed_data.get('received_at', ''),
        'client_ip': parsed_data.get('client_ip', ''),
        'latitude': parsed_data.get('latitude', ''),
        'longitude': parsed_data.get('longitude', ''),
        'manufacturer': parsed_data.get('manufacturer', ''),
        'model': parsed_data.get('model', ''),
        'serial': parsed_data.get('serial', ''),
        'cpu_name': parsed_data.get('cpu_name', ''),
        'cpu_cores': parsed_data.get('cpu_cores', ''),
        'max_clock_speed': parsed_data.get('max_clock_speed', ''),
        'total_ram_gb': parsed_data.get('total_ram_gb', ''),
        'available_ram_mb': parsed_data.get('available_ram_mb', ''),
        'total_storage_gb': parsed_data.get('total_storage_gb', ''),
        'available_storage_gb': parsed_data.get('available_storage_gb', '')
    }

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in existing_data.values():
            writer.writerow(row)

def get_all_analytics():
    """Get analytics for all users"""
    if os.path.exists(ANALYTICS_FILE):
        with open(ANALYTICS_FILE, 'r') as f:
            return json.load(f)
    return {}

def get_user_analytics(username):
    """Get analytics for a specific user"""
    analytics = get_all_analytics()
    if username in analytics:
        return analytics[username]
    return {"error": f"User '{username}' not found"}

def get_all_users():
    """Get list of all tracked users"""
    analytics = get_all_analytics()
    users = []
    for user_id, data in analytics.items():
        users.append({
            "user_id": user_id,
            "username": data.get("username"),
            "computer_name": data.get("computer_name"),
            "last_updated": data.get("last_updated")
        })
    return {"total_users": len(users), "users": users}

if __name__ == "__main__":
    sample_log = """====================================================== 
2025-12-05 05:21:21 - DESKTOP-GO2C520 
====================================================== 
Username: user001
GPS Location: GPS: 10.8406773 , 76.6276741 
Manufacturer: Acer 
Model: Extensa 215-54 
Serial: NXEGJSI00T233047613400 
CPU Name: 11th Gen Intel(R) Core(TM) i3-1115G4 @ 3.00GHz 
CPU Cores: 2 
Max Clock Speed: 2995 MHz 
Total RAM: 15.7844772338867 GB 
Available RAM: 10.7930946350098 MB 
Total Storage C:: 225.28 GB 
Available Storage C: 117.07 GB"""

    result = process_and_store_log(sample_log, "127.0.0.1")
    print(result)
