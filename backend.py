from fastapi import FastAPI, File, Query, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from openai import OpenAI
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import json
import os
import uuid
from typing import List, Optional

load_dotenv()

# --- Key Vault / Secrets setup ---
# Use os.environ for all secrets and config, no Azure Key Vault
OPENAI_KEY = os.environ['PROJ-OPENAI-API-KEY']

# Local image storage directory
LOCAL_IMAGE_DIR = 'images'
os.makedirs(LOCAL_IMAGE_DIR, exist_ok=True)

# --- Local JSON storage setup ---
CHAT_LOGS_DIR = 'chat_logs'
os.makedirs(CHAT_LOGS_DIR, exist_ok=True)
CHATS_INDEX_FILE = os.path.join(CHAT_LOGS_DIR, 'chats_index.json')

def load_chats_index():
    if not os.path.exists(CHATS_INDEX_FILE):
        return []
    with open(CHATS_INDEX_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_chats_index(index):
    with open(CHATS_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

# OpenAI setup
client = OpenAI(api_key=OPENAI_KEY)
model  = "gpt-3.5-turbo"

app = FastAPI()

# --- Pydantic models ---
class ChatRequest(BaseModel):
    messages: List[dict]

class SaveChatRequest(BaseModel):
    chat_id: str
    chat_name: str
    messages: List[dict]
    image_name: Optional[str] = None
    image_url: Optional[str] = None

class DeleteChatRequest(BaseModel):
    chat_id: str

class ImageChatRequest(BaseModel):
    messages: List[dict]
    image_url: str

# --- Endpoints ---

@app.post("/chat/")
async def chat(request: ChatRequest):
    try:
        stream = client.chat.completions.create(
            model=model, messages=request.messages, stream=True
        )
        def streamer():
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        return StreamingResponse(streamer(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/load_chat/")
async def load_chat():
    try:
        index = load_chats_index()
        records = []
        for r in index:
            file_path = r['file_path']
            with open(file_path, "r", encoding="utf-8") as f:
                messages = json.load(f)
                records.append({
                    "id": r["id"],
                    "chat_name": r["name"],
                    "messages": messages,
                    "image_name": r.get("image_name"),
                    "image_url": r.get("image_url")
                })
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_chat/")
async def save_chat(request: SaveChatRequest):
    try:
        file_path = os.path.join(CHAT_LOGS_DIR, f"{request.chat_id}.json")
        # save JSON to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(request.messages, f, ensure_ascii=False, indent=2)
        # update index
        index = load_chats_index()
        found = False
        for chat in index:
            if chat['id'] == request.chat_id:
                chat['name'] = request.chat_name
                chat['file_path'] = file_path
                chat['image_url'] = request.image_url
                chat['image_name'] = request.image_name
                found = True
                break
        if not found:
            index.append({
                'id': request.chat_id,
                'name': request.chat_name,
                'file_path': file_path,
                'image_url': request.image_url,
                'image_name': request.image_name
            })
        save_chats_index(index)
        return {"message": "Chat saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/delete_chat/")
async def delete_chat(request: DeleteChatRequest):
    try:
        index = load_chats_index()
        chat = next((c for c in index if c['id'] == request.chat_id), None)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        file_path = chat['file_path']
        # remove from index
        index = [c for c in index if c['id'] != request.chat_id]
        save_chats_index(index)
        # delete file
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return {"message": "Chat deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_image/")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Only image files allowed")

    try:
        contents = await file.read()
        ext = os.path.splitext(file.filename)[1]
        image_uuid = str(uuid.uuid4())
        local_filename = f"{image_uuid}{ext}"
        local_path = os.path.join(LOCAL_IMAGE_DIR, local_filename)
        with open(local_path, "wb") as f:
            f.write(contents)
        image_url = f"/images/{local_filename}"  # For serving via static files if needed
        return {
            "image_uuid": image_uuid,
            "image_name": file.filename,
            "image_url": image_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/image_recognition/")
async def image_recognition(request: ImageChatRequest):
    try:
        # Prepare messages for OpenAI
        messages = []
        for msg in request.messages:
            if msg["role"] == "user":
                content = [{"type": "text", "text": msg["content"]}]
                if msg == request.messages[-1]:  # Last user message gets the image
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": request.image_url}
                    })
                messages.append({"role": "user", "content": content})
            else:
                messages.append({"role": "assistant", "content": msg["content"]})

        # Stream the response
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True
        )
        
        def stream_generator():
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        return StreamingResponse(stream_generator(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image QA error: {e}")