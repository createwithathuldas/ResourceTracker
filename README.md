# ResourceTracker

A comprehensive resource management system that enables organizations to track and monitor their hardware assets with deep telemetry and health monitoring capabilities.

## Overview

ResourceTracker is a prototype solution designed to help organizations maintain visibility and control over their distributed hardware resources, particularly laptops and workstations. The system combines asset tracking with real-time device health monitoring, providing administrators with detailed insights into device usage, performance metrics, and operational status.

## Key Features

### 🖥️ Asset Management
- **Device Registration**: Seamless onboarding process for new hardware assets
- **User Assignment**: Track which devices are assigned to which users
- **Asset Lifecycle Tracking**: Monitor devices from deployment to retirement

### 📊 Deep Telemetry & Monitoring
- **Device Health Metrics**: Real-time monitoring of hardware health indicators
- **Performance Tracking**: CPU, RAM, disk usage, and other critical metrics
- **Usage Analytics**: Understand how devices are being utilized across your organization

### 🔄 Automated Data Collection
- **Background Agent**: Lightweight client-side script (currently .bat, extensible to shell scripts)
- **Scheduled Execution**: Automatically runs on system startup/restart via cron jobs
- **Offline Capability**: Logs data locally when internet connectivity is unavailable
- **Smart Sync**: Automatically uploads logs to server when internet connection is restored

### 📈 Dashboard & Reporting
- **Visual Dashboard**: Intuitive interface for viewing device status and metrics
- **Multiple Export Formats**: Data available in JSON and CSV formats
- **Historical Analysis**: Track trends and patterns over time
- **Custom Reports**: Generate reports based on specific organizational needs

## How It Works

### 1. Initial Setup
When a user receives a new device:
1. User signs into the ResourceTracker system
2. System prompts download of the monitoring agent (batch/shell script)
3. User executes the downloaded file to initialize monitoring

### 2. Monitoring Agent
The agent performs the following operations:
- Installs itself as a scheduled task/cron job
- Executes automatically on system startup/restart
- Collects device metrics including:
  - CPU utilization
  - RAM usage
  - Disk space and health
  - System uptime
  - Network connectivity status
  - Hardware health indicators
- Writes collected data to local log files

### 3. Data Synchronization
- Agent checks for internet connectivity
- When online, securely transmits log files to central server
- Maintains local logs until successful upload
- Clears uploaded data to optimize storage

### 4. Dashboard & Analysis
- Server processes incoming telemetry data
- Dashboard displays real-time and historical metrics
- Data available for export in JSON/CSV formats
- Administrators can monitor fleet health and identify issues proactively

## Architecture

```
┌─────────────────┐
│   Client Device │
│   ┌─────────┐   │
│   │ Monitor │───┼──► Local Logs
│   │  Agent  │   │
│   └─────────┘   │
└────────┬────────┘
         │ (When Online)
         ▼
┌─────────────────┐
│  Central Server │
│   ┌─────────┐   │
│   │   API   │   │
│   └────┬────┘   │
│        │        │
│   ┌────▼────┐   │
│   │Database │   │
│   └────┬────┘   │
│        │        │
│   ┌────▼────┐   │
│   │Dashboard│   │
│   └─────────┘   │
└─────────────────┘
```

## Current Implementation Status

**Prototype Phase** - Core functionality implemented:
- ✅ User authentication and device registration
- ✅ Windows monitoring agent (.bat script)
- ✅ Local logging mechanism
- ✅ Automatic sync to server
- ✅ Basic dashboard with data visualization
- ✅ JSON/CSV export functionality

**Planned Enhancements**:
- Cross-platform agent support (Linux/macOS shell scripts)
- Enhanced security features (encryption, authentication tokens)
- Advanced alerting and notifications
- Mobile dashboard access
- Predictive maintenance capabilities

## Use Cases

- **IT Asset Management**: Track all organizational devices from a central location
- **Compliance Monitoring**: Ensure devices meet organizational standards
- **Proactive Maintenance**: Identify failing hardware before critical failures
- **Resource Optimization**: Understand usage patterns to optimize hardware allocation
- **Remote Fleet Management**: Monitor distributed teams' devices effectively

## Technical Requirements

### Client-Side
- Windows OS (current implementation)
- Administrator privileges for initial setup
- Periodic internet connectivity for data sync

### Server-Side
- Web server with API capabilities
- Database for storing telemetry data
- Dashboard hosting environment

## Security Considerations

- All data transmission should be encrypted (HTTPS)
- User authentication required for device registration
- Local logs should be protected from unauthorized access
- Regular security audits recommended for production deployment

## Getting Started

-fork
-clone
-work 
-push
-pull request

## Contributing

This is currently a prototype project. Contributions, suggestions, and feedback are welcome as we work towards a production-ready release.

## Contact & Support

*Athul Das
[Connect and Message in LinkedIn](https://www.linkedin.com/in/athul-das-760105284?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3BogmJn0cRTcyGK6MUIM%2FGCQ%3D%3D)

---

**Note**: ResourceTracker is currently in prototype phase. Features and functionality are subject to change as the project evolves.
