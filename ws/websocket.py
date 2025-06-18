import logging

from fastapi import WebSocket, APIRouter, WebSocketDisconnect

router = APIRouter()

logging.basicConfig(level=logging.INFO)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)

    async def send_message(self, session_id: str, message: str):
        logging.info(f"[Websocket] Send message: {message} to Session: {session_id}")
        websocket = self.active_connections.get(session_id)
        logging.info(f"Websocket: {websocket}")
        if websocket:
            await websocket.send_text(message)
        else:
            logging.error(f"No websocket: {websocket} found")


websocket_manager = ConnectionManager()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket_manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager.send_message(session_id, f"You wrote: {data}")
    except WebSocketDisconnect:
        websocket_manager.disconnect(session_id)