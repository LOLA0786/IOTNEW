from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from apps.prod_api.publisher import register, unregister
from typing import List

router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("/events")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await register(websocket)
    try:
        while True:
            # keep connection open; receive ping/pong
            await websocket.receive_text()
    except WebSocketDisconnect:
        await unregister(websocket)
    except Exception:
        await unregister(websocket)
