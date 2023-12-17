from fastapi import WebSocket
from typing import Dict

class ConnectionManager:
    def __init__(self):
        # self.active_connections: list[WebSocket] = []
        self.active_connections: Dict[str, list[WebSocket]] = {"": []}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
#        self.active_connections.append(websocket)
        if room_id not in self.active_connections:
            self.active_connections.update({room_id: [websocket]})
        else:
            self.active_connections[room_id].append(websocket)


    def disconnect(self, room_id: str, websocket: WebSocket):
        room = self.active_connections[room_id]
        room.remove(websocket)
        if len(room) == 0:
            del room

    async def send_personal_message(self, message: str, room_id:str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, room_id: str, self_websocket: WebSocket):
        for connection in self.active_connections[room_id]:
            if connection is not self_websocket:
                await connection.send_text(message)
            else: pass
