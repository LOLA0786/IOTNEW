import asyncio, os, json, time
import aiohttp

RUN_MULTI_URL = os.getenv("LOCAL_RUN_MULTI", "http://localhost:7000/run-multi")
DEFAULT_SYMBOLS = os.getenv("SCHED_SYMBOLS", "AAPL,NVDA,MSFT").split(",")

async def call_run_multi(symbols):
    async with aiohttp.ClientSession() as sess:
        try:
            async with sess.post(RUN_MULTI_URL, json={"symbols": symbols, "session_id": f"sched-{int(time.time())}"}, timeout=60) as r:
                try:
                    return await r.json()
                except:
                    return {"error": "invalid response"}
        except Exception as e:
            return {"error": str(e)}

async def scheduler_loop(interval_seconds:int = 300):
    """
    Runs forever; call in background or via separate process.
    Default: every 5 minutes (300s)
    """
    while True:
        try:
            res = await call_run_multi(DEFAULT_SYMBOLS)
            print("scheduler run:", res)
        except Exception as e:
            print("scheduler error:", e)
        await asyncio.sleep(interval_seconds)

def start_background(interval_seconds:int = 300):
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler_loop(interval_seconds))
    return loop

if __name__ == "__main__":
    asyncio.run(scheduler_loop(300))
