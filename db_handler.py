import mysql.connector
from mysql.connector import Error
import json
import os
from datetime import datetime, timedelta

# Database configuration - UPDATE THESE!
DB_CONFIG = {
    "host": "localhost",
    "database": "device_management",
    "user": "root",
    "password": "password",  # your real password
}

DATA_DIR = "processed_data"


def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def _format_dt(row: dict, keys):
    """Convert datetime fields in-place to str."""
    for k in keys:
        if row.get(k):
            row[k] = row[k].strftime("%Y-%m-%d %H:%M:%S")


def get_all_users_db():
    """All users for cards (with device count & last activity)."""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                u.id,
                u.name,
                u.email,
                u.role,
                u.created_at,
                COUNT(DISTINCT a.device_id)     AS device_count,
                MAX(al.timestamp)               AS last_activity
            FROM user u
            LEFT JOIN assignment a
                ON u.id = a.user_id AND a.status = 'approved'
            LEFT JOIN audit_log al
                ON u.id = al.user_id
            GROUP BY
                u.id, u.name, u.email, u.role, u.created_at
            ORDER BY u.name
        """
        cursor.execute(query)
        users = cursor.fetchall()

        for user in users:
            _format_dt(user, ["created_at", "last_activity"])
        return users

    except Error as e:
        print(f"Error fetching users: {e}")
        return []
    finally:
        conn.close()


def get_user_details(user_id: int):
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, email, role, created_at "
            "FROM user WHERE id = %s",
            (user_id,),
        )
        user = cursor.fetchone()
        if user:
            _format_dt(user, ["created_at"])
        return user

    except Error as e:
        print(f"Error fetching user details: {e}")
        return None
    finally:
        conn.close()


def get_user_devices(user_id: int):
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                d.id,
                d.name,
                d.serial,
                d.category,
                d.status,
                d.condition,
                d.location,
                d.created_at,
                a.status       AS assignment_status,
                a.assigned_at,
                a.purpose,
                a.requested_at
            FROM device d
            JOIN assignment a
                ON d.id = a.device_id
            WHERE a.user_id = %s
              AND a.status IN ('approved', 'pending')
            ORDER BY a.assigned_at DESC
        """
        cursor.execute(query, (user_id,))
        devices = cursor.fetchall()

        for dev in devices:
            _format_dt(dev, ["created_at", "assigned_at", "requested_at"])
        return devices

    except Error as e:
        print(f"Error fetching user devices: {e}")
        return []
    finally:
        conn.close()


def get_device_details(device_id: int):
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, serial, category, status, "
            "condition, location, created_at "
            "FROM device WHERE id = %s",
            (device_id,),
        )
        device = cursor.fetchone()
        if device:
            _format_dt(device, ["created_at"])
        return device

    except Error as e:
        print(f"Error fetching device: {e}")
        return None
    finally:
        conn.close()


def get_usage_analytics():
    """High‑level analytics for charts (DB + logs)."""
    analytics = {
        "user_device_count": [],
        "category_distribution": [],
        "status_distribution": [],
        "resource_usage": [],
    }

    conn = get_db_connection()
    if not conn:
        return analytics

    try:
        cursor = conn.cursor(dictionary=True)

        # Devices per user
        cursor.execute(
            """
            SELECT
                u.name,
                COUNT(a.device_id) AS device_count
            FROM user u
            LEFT JOIN assignment a
                ON u.id = a.user_id AND a.status = 'approved'
            GROUP BY u.id, u.name
            HAVING device_count > 0
        """
        )
        analytics["user_device_count"] = cursor.fetchall()

        # Device categories
        cursor.execute(
            "SELECT category, COUNT(*) AS count "
            "FROM device GROUP BY category"
        )
        analytics["category_distribution"] = cursor.fetchall()

        # Device status distribution
        cursor.execute(
            "SELECT status, COUNT(*) AS count "
            "FROM device GROUP BY status"
        )
        analytics["status_distribution"] = cursor.fetchall()

        # Resource usage from logs
        analytics["resource_usage"] = get_resource_usage_from_logs()

        return analytics

    except Error as e:
        print(f"Error fetching analytics: {e}")
        return analytics
    finally:
        conn.close()


def get_resource_usage_from_logs():
    """Read processed_data/analytics.json and compute usage %."""
    usage_data = []
    analytics_file = os.path.join(DATA_DIR, "analytics.json")

    if not os.path.exists(analytics_file):
        return usage_data

    with open(analytics_file, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    for user_id, data in all_data.items():
        memory = data.get("memory", {})
        storage = data.get("storage", {})

        total_ram = memory.get("total_ram_gb", 0) or 0
        available_ram = memory.get("available_ram_mb", 0) or 0
        total_storage = storage.get("total_gb", 0) or 0
        available_storage = storage.get("available_gb", 0) or 0

        ram_used_pct = (
            (total_ram * 1024 - available_ram) / (total_ram * 1024) * 100
            if total_ram > 0
            else 0
        )
        storage_used_pct = (
            (total_storage - available_storage) / total_storage * 100
            if total_storage > 0
            else 0
        )

        usage_data.append(
            {
                "user_id": user_id,
                "username": data.get("username", user_id),
                "computer_name": data.get("computer_name", "Unknown"),
                "ram_total_gb": round(total_ram, 2),
                "ram_used_pct": round(ram_used_pct, 1),
                "storage_total_gb": round(total_storage, 2),
                "storage_used_pct": round(storage_used_pct, 1),
                "last_updated": data.get("last_updated", ""),
            }
        )

    return usage_data


def get_resource_alerts():
    """Generate over/under‑usage alerts from log analytics."""
    alerts = []
    usage_data = get_resource_usage_from_logs()

    for data in usage_data:
        user = data["username"]

        ram_pct = data["ram_used_pct"]
        if ram_pct > 85:
            alerts.append(
                {
                    "type": "danger",
                    "category": "RAM",
                    "user": user,
                    "message": f"High RAM usage: {ram_pct}%",
                    "value": ram_pct,
                    "threshold": 85,
                    "recommendation": "Consider closing unused applications or upgrading RAM",
                }
            )
        elif ram_pct < 20:
            alerts.append(
                {
                    "type": "warning",
                    "category": "RAM",
                    "user": user,
                    "message": f"Low RAM utilization: {ram_pct}%",
                    "value": ram_pct,
                    "threshold": 20,
                    "recommendation": "Device may be over-provisioned for user needs",
                }
            )

        storage_pct = data["storage_used_pct"]
        if storage_pct > 90:
            alerts.append(
                {
                    "type": "danger",
                    "category": "Storage",
                    "user": user,
                    "message": f"Critical storage usage: {storage_pct}%",
                    "value": storage_pct,
                    "threshold": 90,
                    "recommendation": "Immediate cleanup or storage expansion needed",
                }
            )
        elif storage_pct > 75:
            alerts.append(
                {
                    "type": "warning",
                    "category": "Storage",
                    "user": user,
                    "message": f"High storage usage: {storage_pct}%",
                    "value": storage_pct,
                    "threshold": 75,
                    "recommendation": "Plan for storage cleanup soon",
                }
            )
        elif storage_pct < 15:
            alerts.append(
                {
                    "type": "info",
                    "category": "Storage",
                    "user": user,
                    "message": f"Low storage utilization: {storage_pct}%",
                    "value": storage_pct,
                    "threshold": 15,
                    "recommendation": "Device storage may be over-provisioned",
                }
            )

    return alerts
