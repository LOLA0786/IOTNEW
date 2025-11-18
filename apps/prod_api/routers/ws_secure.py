from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from apps.prod_api.auth import verify_api_key, decode_jwt

router = APIRouter(prefix="/ws-secure", tags=["WebSocketSecure"])


@router.websocket("/events")
async def websocket_events(ws: WebSocket):
    await ws.accept()
    # expect first message to be auth key or token
    try:
        auth = await ws.receive_text()
        # allow either api key or jwt
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
            if not decode_jwt(token):
                await ws.close(code=4401)
                return
        else:
            if not verify_api_key(auth):
                await ws.close(code=4401)
                return
        # now keep sending messages (or receive pings)
        while True:
            msg = await ws.receive_text()  # echo-style to keep alive
            await ws.send_text("pong:" + msg)
    except WebSocketDisconnect:
        return
