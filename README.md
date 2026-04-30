# Mission-Critical Incident Management System (IMS)

A production-grade, distributed SRE system built for high-throughput signal processing, atomic debouncing, and strict workflow enforcement.

## 🏗️ Architecture Overview

```text
  [ High-Volume Signals ] (10k/sec)
            |
            v
    +-------------------+
    |   FastAPI Ingest  | ----> [ Redis Buffer Queue ]
    +-------------------+               |
                                        v
                                +------------------+
                                |  Async Workers   |
                                +------------------+
                                 /       |        \
          (State Pattern)       /        |         \   (Strategy Pattern)
         [ PostgreSQL ] <------+   [ MongoDB ]      +----> [ Alerting ]
       (Work Items/RCA)          (Raw Signals)          (P0/P1/P2)
```

### 1. Backpressure & Scaling
The system handles bursts of **10,000 signals/sec** using a **Redis-backed async worker model**. The Ingestion API immediately offloads signals to a Redis list (`signals_queue`), allowing the API to remain responsive while workers process data at their own pace.

### 2. Atomic Debouncing
To prevent incident storms, the worker implements **Strict Debouncing** using a Redis TTL window (10s). 
- Multiple signals for the same component in the window are grouped into a single transactional Work Item in PostgreSQL.
- The `signal_count` is incremented atomically, and all raw payloads are linked in MongoDB for auditability.

### 3. Design Patterns
- **State Pattern**: Managed in `backend/patterns.py`. Enforces strict transitions (OPEN -> INVESTIGATING -> RESOLVED -> CLOSED) and mandatory RCA validation.
- **Strategy Pattern**: Alerting logic is decoupled into `P0AlertStrategy`, `P1AlertStrategy`, etc., allowing for dynamic switching of notification channels based on severity.

### 4. Database Separation (Production Standard)
- **PostgreSQL**: Transactional storage for Work Items, RCAs, and relational metadata.
- **MongoDB**: Schema-less Data Lake for long-term audit logs and raw signal payloads.
- **Redis**: In-memory buffer for backpressure handling and real-time minutely aggregations.

## 🚀 Deployment

```bash
docker compose up --build
```

- **Dashboard**: `http://localhost:5173`
- **Health (SRE View)**: `http://localhost:8000/health`
- **API Docs**: `http://localhost:8000/docs`
