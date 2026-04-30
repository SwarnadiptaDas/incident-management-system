from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import json
import asyncio
from datetime import datetime
import time

from database import get_db, redis_client, signals_collection, engine
from models import Base, WorkItem, StateEnum
from schemas import SignalCreate, WorkItemResponse, RCASubmit
from patterns import WorkflowEngine
from config import settings

app = FastAPI(title="Production-Grade Incident Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- OBSERVABILITY: Structured Logs & Metrics ---
throughput_metrics = {"count": 0, "last_reset": time.time()}

async def observability_logger():
    """Prints structured throughput logs every 5 seconds."""
    while True:
        await asyncio.sleep(5)
        elapsed = time.time() - throughput_metrics["last_reset"]
        if elapsed > 0:
            tps = throughput_metrics["count"] / elapsed
            print(f"[METRICS] Processed {tps:.2f} signals/sec | Buffer Queue Depth: {await redis_client.llen('signals_queue')}")
        throughput_metrics["count"] = 0
        throughput_metrics["last_reset"] = time.time()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    asyncio.create_task(observability_logger())

@app.get("/health")
async def deep_health_check(db: AsyncSession = Depends(get_db)):
    """
    Enhanced Health Endpoint: Returns status of all system dependencies.
    """
    health = {"status": "ok", "dependencies": {}}
    
    # Check PostgreSQL
    try:
        await db.execute(select(1))
        health["dependencies"]["postgres"] = "healthy"
    except Exception:
        health["dependencies"]["postgres"] = "unhealthy"
        health["status"] = "degraded"

    # Check Redis
    try:
        await redis_client.ping()
        health["dependencies"]["redis"] = "healthy"
    except Exception:
        health["dependencies"]["redis"] = "unhealthy"
        health["status"] = "degraded"

    # Check MongoDB
    try:
        await signals_collection.database.command("ping")
        health["dependencies"]["mongodb"] = "healthy"
    except Exception:
        health["dependencies"]["mongodb"] = "unhealthy"
        health["status"] = "degraded"
        
    return health

@app.post("/api/signals")
async def ingest_signal(signal: SignalCreate, request: Request):
    """
    INGESTION: Handles high-throughput signals using a non-blocking Redis Queue.
    Architecture: Implements Backpressure Handling via Buffer.
    """
    # Simple Rate Limiting
    client_ip = request.client.host
    rate_limit_key = f"rate:{client_ip}"
    if (await redis_client.incr(rate_limit_key)) == 1:
        await redis_client.expire(rate_limit_key, 60)
    
    if int(await redis_client.get(rate_limit_key)) > settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Push to Backpressure Buffer (Redis)
    signal_dict = signal.model_dump()
    signal_dict["timestamp"] = signal_dict["timestamp"].isoformat()
    await redis_client.lpush("signals_queue", json.dumps(signal_dict))
    
    throughput_metrics["count"] += 1
    return {"status": "queued", "component_id": signal.component_id}

@app.get("/api/incidents", response_model=List[WorkItemResponse])
async def list_incidents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WorkItem).order_by(WorkItem.state.desc(), WorkItem.start_time.desc())
    )
    return result.scalars().all()

@app.get("/api/incidents/{incident_id}/signals")
async def get_raw_signals(incident_id: int):
    """Retrieves raw signals from the MongoDB Data Lake."""
    cursor = signals_collection.find({"work_item_id": incident_id}).sort("timestamp", -1)
    signals = await cursor.to_list(length=1000)
    for s in signals:
        s["_id"] = str(s["_id"])
    return signals

@app.get("/api/metrics/{component_id}")
async def get_timeseries_stats(component_id: str):
    """Retrieves signal-per-minute aggregation from Redis."""
    now = datetime.utcnow()
    key = f"ims:agg:{component_id}:{now.strftime('%Y%m%d%H%M')}"
    count = await redis_client.get(key)
    return {"component_id": component_id, "signals_per_min": int(count) if count else 0}

@app.post("/api/incidents/{incident_id}/rca", response_model=WorkItemResponse)
async def submit_rca(incident_id: int, rca: RCASubmit, db: AsyncSession = Depends(get_db)):
    """
    RCA SUBMISSION: Updates work item with remediation details and closes it.
    Strictly enforced by the State Pattern.
    """
    result = await db.execute(select(WorkItem).where(WorkItem.id == incident_id))
    work_item = result.scalar_one_or_none()
    
    if not work_item:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    # Apply RCA details
    work_item.rca_category = rca.rca_category
    work_item.fix_applied = rca.fix_applied
    work_item.prevention_steps = rca.prevention_steps
    work_item.end_time = datetime.utcnow()
    
    # Calculate MTTR
    delta = work_item.end_time - work_item.start_time
    work_item.mttr_minutes = delta.total_seconds() / 60.0
    
    # Transition State strictly via WorkflowEngine
    try:
        # Move to RESOLVED then CLOSED to satisfy State Pattern rules
        if work_item.state == StateEnum.OPEN:
            WorkflowEngine.transition(work_item, StateEnum.INVESTIGATING)
        if work_item.state == StateEnum.INVESTIGATING:
            WorkflowEngine.transition(work_item, StateEnum.RESOLVED)
        
        # This will fail if RCA fields are missing
        WorkflowEngine.transition(work_item, StateEnum.CLOSED)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    await db.commit()
    await db.refresh(work_item)
    return work_item
