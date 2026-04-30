import asyncio
import aiohttp
import json
from datetime import datetime, timezone

API_URL = "http://localhost:8000/api/signals"

async def send_signal(session, component_id, error, severity):
    payload = {
        "component_id": component_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error": error,
        "severity": severity
    }
    try:
        async with session.post(API_URL, json=payload) as response:
            if response.status == 200:
                print(f"✅ Sent {severity} for {component_id}")
            else:
                print(f"❌ Failed ({response.status}) for {component_id}: {await response.text()}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

async def simulate_outage():
    async with aiohttp.ClientSession() as session:
        print("Simulating RDBMS Outage (P0)...")
        # Burst of P0 signals for database
        tasks = []
        for i in range(10):
            tasks.append(send_signal(session, "db-cluster-main", f"Connection timeout on shard {i}", "P0"))
        
        await asyncio.gather(*tasks)
        
        await asyncio.sleep(2)
        
        print("\nSimulating Cache Failure (P1)...")
        # Burst of P1 signals for cache
        tasks = []
        for i in range(5):
            tasks.append(send_signal(session, "redis-cache-eu", "Eviction limit reached, latency spikes", "P1"))
        
        await asyncio.gather(*tasks)
        
        await asyncio.sleep(2)
        
        print("\nSimulating Minor Service Flap (P3)...")
        # P3 signals spread out
        for i in range(3):
            await send_signal(session, "auth-service-node", "Slow response time (500ms)", "P3")
            await asyncio.sleep(1)

if __name__ == "__main__":
    print("Ensure the backend API is running at http://localhost:8000")
    asyncio.run(simulate_outage())
