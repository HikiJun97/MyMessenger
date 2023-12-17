from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from ConnectionManager import ConnectionManager
import aiohttp
import json
import base64
from pprint import pprint
from PIL import Image
from io import BytesIO

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
# llm_url = 'http://210.106.97.144:28001/generate'
llm_url = 'http://minirecord.iptime.org:8002/generate'
fuyu_url = 'http://minirecord.iptime.org:8888/image'

manager = ConnectionManager()

def make_prompt(prompt: str) -> dict:
    body = {
        "prompt": "[INST] 대답에 적절히 반응한다.\n[USER] " + prompt + " [/USER][/INST]\n[ANSWER]",
        "max_tokens": 8192,
        "temperature": 0.3,
        "top_k": 10,
        "frequency_penalty": 1.1
    }
    return body

@app.get("/", response_class=HTMLResponse)
async def get():
    with open('messenger.html', 'r') as f:
        return f.read()

@app.websocket("/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(room_id, websocket)
    client_id = await websocket.receive_text()
    print("client_id:", client_id)
    try:
        while True:
            # data = await websocket.receive_text()
            data = await websocket.receive_json()
            print(f"{room_id}: {client_id}")
            # json_data = json.loads(data)
            async with aiohttp.ClientSession() as session:
                if "text" in data:
                    
                    # response = await session.post(url=llm_url, json=make_prompt(json_data.get("text")))
                    # response_json = await response.json()
                    # await websocket.send_text(response_json.get("text"))
                    # data = await websocket.receive_text()
                    # await manager.send_personal_message(f"{data}", room_id, websocket)
                    print(f"text: {data.get('text')}")
                    await manager.broadcast(f"{client_id}: {data.get('text')}", room_id, websocket)
                elif "image" in data:
                    response = await session.post(url=fuyu_url, json={"image": data.get("image")})
                    response_json = await response.json()
                    print(response_json)
                    await websocket.send_text(response_json.get("msg"))
    
                    # image_data = base64.b64decode(json_data.get("image").split(',')[1])
                    # rgb_image = Image.open(BytesIO(image_data))
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        await manager.broadcast(f"Client <{client_id}> left the chat", room_id, websocket)
    except Exception as e:
        print(e)
    finally:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app="websocket_server:app", host="0.0.0.0", port=8001, reload=True)

