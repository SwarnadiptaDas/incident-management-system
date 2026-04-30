import asyncio
import json
from datetime import datetime
from sqlalchemy import update
from database import redis_client, signals_collection, AsyncSessionLocal
from models import WorkItem, SeverityEnum, StateEnum
from patterns import get_alert_strategy
import logging

# Structured Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("ims_worker")

async def update_aggregation(component_id: str):
    """Simple Time-Series Aggregation: Count signals per minute per component in Redis."""
    agg_key = f"ims:agg:{component_id}:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
    await redis_client.incr(agg_key)
    await redis_client.expire(agg_key, 3600) # Retention: 1 hour

async def process_signal(signal_data: dict):
    component_id = signal_data["component_id"]
    severity = signal_data["severity"]
    
    await update_aggregation(component_id)
    
    # =========================================================================
    # DEBOUNCING LOGIC (STRICT)
    # This uses Redis TTL with a 10-second window to prevent duplicate incidents.
    # If a signal for the same component arrives within the window, we increment
    # the counter on the existing Work Item instead of creating a new one.
    # =========================================================================
    debounce_key = f"debounce:{component_id}"
    active_wi_id = await redis_client.get(debounce_key)
    
    async with AsyncSessionLocal() as session:
        if active_wi_id:
            work_item_id = int(active_wi_id)
            # Increment signal count atomically in PostgreSQL
            await session.execute(
                update(WorkItem)
                .where(WorkItem.id == work_item_id)
                .values(signal_count=WorkItem.signal_count + 1)
            )
            await session.commit()
            # Extend debouncing window by 10s
            await redis_client.expire(debounce_key, 10)
            logger.info(f"DEBOUNCED: Linked signal to existing Work Item #{work_item_id} for {component_id}")
        else:
            # Create NEW Work Item (Transactional)
            try:
                sev_enum = SeverityEnum(severity)
            except ValueError:
                sev_enum = SeverityEnum.P3
                
            new_work_item = WorkItem(
                component_id=component_id,
                severity=sev_enum,
                state=StateEnum.OPEN,
                signal_count=1
            )
            session.add(new_work_item)
            await session.commit()
            await session.refresh(new_work_item)
            
            work_item_id = new_work_item.id
            # Set debounce lock in Redis (10s window)
            await redis_client.setex(debounce_key, 10, str(work_item_id))
            
            # Switch alerting logic based on Strategy Pattern
            strategy = get_alert_strategy(sev_enum)
            strategy.alert(signal_data, work_item_id)
            logger.info(f"NEW INCIDENT: Created Work Item #{work_item_id} for {component_id}")
    
    # =========================================================================
    # ARCHITECTURE: DATABASE SEPARATION
    # MongoDB → Raw signals (Audit Log / Data Lake)
    # PostgreSQL → Work items + RCA (Transactional / Source of Truth)
    # =========================================================================
    signal_data["timestamp"] = datetime.fromisoformat(signal_data["timestamp"])
    signal_data["work_item_id"] = work_item_id # FK link between Postgres and Mongo
    
    try:
        await signals_collection.insert_one(signal_data)
    except Exception as e:
        logger.error(f"DATABASE ERROR (Mongo): {e}")

async def main():
    logger.info("IMS WORKER LIVE - Buffering signals via Redis Queue...")
    while True:
        try:
            # Backpressure Handling: Pull from Redis Queue
            result = await redis_client.brpop("signals_queue", timeout=0)
            if result:
                _, item = result
                await process_signal(json.loads(item))
        except Exception as e:
            logger.error(f"WORKER CRITICAL ERROR: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
