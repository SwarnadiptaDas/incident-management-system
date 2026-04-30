# Sentinel-IMS: Distributed Incident Management System

[![SRE-Ready](https://img.shields.io/badge/SRE-Ready-blue?style=for-the-badge)](https://github.com/SwarnadiptaDas/incident-management-system)
[![Architecture-Distributed](https://img.shields.io/badge/Architecture-Distributed-orange?style=for-the-badge)](https://github.com/SwarnadiptaDas/incident-management-system)

**Sentinel-IMS** is a production-grade, mission-critical incident management engine designed to handle extreme ingestion bursts (10k+ signals/sec) while maintaining strict transactional integrity and observability.

---

## 🏗️ High-Level Architecture

The system utilizes a **Decoupled Async Architecture** to separate high-frequency signal ingestion from complex business logic and persistence.

```text
                                [ EXTERNAL STACK ]
                               (APIs, DBs, Cache)
                                       |
                                       v (10k signals/sec)
    +-------------------+      +-------------------+
    |   Sentinel API    | ---> |  Redis Ingestion  |
    |   (FastAPI/uvloop)|      |  (Buffer Queue)   |
    +-------------------+      +-------------------+
                                       |
                                       v (BRPOP)
    +-------------------+      +-------------------+
    |  Workflow Engine  | <--- |  Sentinel Worker  |
    |  (State Pattern)  |      |  (Async Logic)    |
    +-------------------+      +-------------------+
             |                         |
             v                         v
    +-------------------+      +-------------------+
    |  PostgreSQL (SoT) |      |  MongoDB (Audit)  |
    |  (Work Items/RCA) |      |  (Raw Payloads)   |
    +-------------------+      +-------------------+
```

---

## 🛡️ Core Pillars of Resilience

### 1. High-Throughput & Backpressure
Sentinel-IMS leverages **Redis as a shock absorber**. When a failure storm occurs, signals are buffered in a high-speed list, allowing the API to remain responsive while the workers consume data at an optimal pace.

### 2. Atomic Debouncing (Strict Windowing)
To prevent "Alert Fatigue" and DB locking, the system implements a **10-second Atomic Debouncing Window**.
- Multiple identical signals are collapsed into a **single Work Item**.
- A `signal_count` is incremented atomically to track the error density.
- All raw signal payloads are persisted in the **NoSQL Data Lake** for post-mortem analysis.

### 3. Design Pattern Excellence
- **State Pattern**: Enforces a strict lifecycle (OPEN → INVESTIGATING → RESOLVED → CLOSED). It prevents invalid transitions and mandates RCA details before an incident can be archived.
- **Strategy Pattern**: Decouples alerting logic. Based on severity (P0-P3), the engine dynamically switches between immediate paging, Slack notifications, or simple logging.

### 4. Deep Observability
- **Minutely Aggregation**: Real-time timeseries tracking of signal frequency per component.
- **Health Engine**: A comprehensive `/health` endpoint that monitors the heartbeat of PostgreSQL, MongoDB, Redis, and Worker connectivity.

---

## 🔌 API Reference

### Signal Ingestion
`POST /api/signals`
```json
{
  "component_id": "rdbms_cluster_01",
  "error": "Connection Timeout",
  "severity": "P0"
}
```

### Metrics & Aggregation
`GET /api/metrics/{component_id}`
Returns minutely throughput data for the specified component.

---

## 🚀 Deployment Guide

### Prerequisites
- Docker & Docker Compose
- Ubuntu WSL (Recommended for native performance)

### Fast Launch
```bash
# Clone the repository
git clone https://github.com/SwarnadiptaDas/incident-management-system.git
cd incident-management-system

# Launch the entire stack
docker compose up --build -d
```

### Dashboards
- **Monitoring Portal**: `http://localhost:5173`
- **SRE Health View**: `http://localhost:8000/health`
- **Interactive API Docs**: `http://localhost:8000/docs`

---

## 🧪 Simulation
To test the resilience under load, run the provided simulation script:
```bash
python3 simulate_signals.py
```
This script triggers multiple failure scenarios across the stack to demonstrate debouncing and state management.

---
**Developed with 💙 for SRE & Infrastructure Excellence.**
