from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import time, os, asyncio

router = APIRouter()

LOG_PATH = os.getenv("IOA_LOG_PATH", "/tmp/ioa_logs.txt")

async def tail_file(path):
    # opens file and yields new lines as they appear
    try:
        with open(path, "r") as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                # SSE format: data: <line>\n\n
                yield f"data: {line.strip()}\n\n"
    except FileNotFoundError:
        # emit a notice and keep waiting
        while True:
            yield f"data: {{\"notice\":\"log_not_found\"}}\n\n"
            await asyncio.sleep(2)

@router.get("/stream")
async def stream(request: Request):
    """
    Server-Sent Events endpoint streaming ioa logs.
    Connect via EventSource in browser:
    new EventSource('/stream')
    """
    generator = tail_file(LOG_PATH)
    return StreamingResponse(generator, media_type="text/event-stream")
