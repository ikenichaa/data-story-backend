import logging

from fastapi import FastAPI, WebSocket, APIRouter

router = APIRouter()

logging.basicConfig(level=logging.INFO)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")