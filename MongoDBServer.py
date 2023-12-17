from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError
from fastapi import FastAPI, Request
from pydantic import BaseModel

from bson import ObjectId
import datetime


"""
room_document: {
    "_id": ObjectId,
    "name": str,
    "created_at": datetime.datetime.now().isoformat(),
    "room_id": int
}
"""

SUCCESS_MSG = "New chat room inserted successfully."

class RoomData(BaseModel):
    """Room data schema"""
    name: str
    password: str

app = FastAPI()
client = MongoClient('mongodb://localhost:27017/')

messenger_db = client['messenger_db']
chat_col = messenger_db['chat_col']
room_col = messenger_db['room_col']

def checkIndex():
    existing_indexes = room_col.index_information()
    print(f"existing_indexes: {existing_indexes}")
    
    key = 'room_id_1'
    if key not in existing_indexes:
        room_col.create_index('room_id', unique=True)
        print(f"Index on {key} was created.")
    else:
        print(f"Index on {key} already exists.")

def documentSerializer(doc) -> str:
    obj = doc.get('_id')
    if isinstance(obj, ObjectId):
        doc.update({'_id': str(obj)})
        return doc  # 이미 직렬화되어있으므로 json.dumps(doc) 할 필요없음
    raise TypeError("Type not serializable")

@app.post("/create_room")
async def createRoom(room_data: RoomData):
    room_dict = dict(room_data)
    room_count = countRoom()
    room_dict.update({'created_at': datetime.datetime.now().isoformat(),
                      'room_id': room_count,
                      'users': ['user1', 'user2']
                      })
    while(True):
        try:
            room_col.insert_one(room_dict)  # pymongo는 전달된 document 객체에도 '_id' 필드를 삽입
            print(SUCCESS_MSG)
            break
        except DuplicateKeyError:
            print("Chat room with same room_id already exists.")
            room_dict.update({'room_id': room_count + 1})
    return {"msg": SUCCESS_MSG, "Room Info": documentSerializer(room_dict)}

@app.get("/find_room")
async def findRoom() -> dict:
    room_id_query = {'room_id': {}}
    document_count = room_col.count_documents(room_id_query)
    print(f"room counts: {document_count}")
    room_list = []
    for room in room_col.find({}):
        room_list.append(documentSerializer(room))
    return {'room_list': room_list}

@app.patch("/add_user")
async def addUser(request: Request):
    request_json = await request.json()
    room = room_col.find_one_and_update({'room_id': request_json.get('room_id')},
                                        {'$addToSet': {'users': request_json.get('user_id')}},
                                        return_document=ReturnDocument.AFTER)  # 해당 옵션이 있어야 업데이트 이후의 객체를 반환
    return documentSerializer(room)

@app.delete("/delete_all_room")
async def deleteAllRoom():
    room_col.delete_many({})
    return "All rooms deleted"

def countRoom() -> int:
    room_num_query = {'room_num': {}}
    return room_col.count_documents(room_num_query)

if __name__ == "__main__":
    import uvicorn
    checkIndex()
    uvicorn.run(app='MongoDBServer:app', host='0.0.0.0', port=8001, reload=True)
