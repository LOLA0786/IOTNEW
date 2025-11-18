import asyncio
from typing import Set
import json

# set of WebSocket send coroutines
clients: Set = set()

async def register(ws):
    clients.add(ws)

async def unregister(ws):
    try:
        clients.remove(ws)
    except KeyError:
        pass

async def publish_event(obj: dict):
    """
    Broadcast JSON object to all connected websockets.
    Non-blocking; ignores broken clients.
    """
    if not clients:
        return
    msg = json.dumps(obj)
    to_remove = []
    for ws in list(clients):
        try:
            await ws.send_text(msg)
        except Exception:
            to_remove.append(ws)
    for r in to_remove:
        try:
            clients.remove(r)
        except Exception:
            pass
