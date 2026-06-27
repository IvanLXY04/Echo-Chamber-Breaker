import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from app.orchestrator import orchestrator
from app.policy_server import policy_server
import app.db as db

app = FastAPI()

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    persona: str = "Socratic"
    difficulty: str = "Normal"

class CreateChatRequest(BaseModel):
    email: str
    persona: str = "Socratic"
    difficulty: str = "Normal"

class UpdateChatNameRequest(BaseModel):
    name: str

@app.post("/chats")
async def create_chat(req: CreateChatRequest):
    chat_name = f"Debate: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    chat_id = db.create_chat(req.email, chat_name, req.persona, req.difficulty)
    return {"id": chat_id, "name": chat_name, "persona": req.persona, "difficulty": req.difficulty}

@app.get("/chats")
async def get_chats(email: str):
    chats = db.get_chats_by_email(email)
    return chats

@app.get("/chats/{chat_id}")
async def get_chat_history(chat_id: int):
    messages = db.get_messages(chat_id)
    return messages

@app.put("/chats/{chat_id}/name")
async def update_chat_name(chat_id: int, req: UpdateChatNameRequest):
    db.update_chat_name(chat_id, req.name)
    return {"status": "success"}

@app.post("/chats/{chat_id}/message")
async def chat(chat_id: int, chat_req: ChatRequest):
    try:
        # Save user message
        db.add_message(chat_id, "user", chat_req.message)
        
        # Get history
        history = db.get_messages(chat_id)
        
        # Process turn
        result = orchestrator.process_turn(chat_req.message, chat_req.persona, chat_req.difficulty, history)
        
        # Save AI responses
        db.add_message(chat_id, "opponent", result["opponent_response"], result["referee_scorecard"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chats/{chat_id}/report")
async def generate_report(chat_id: int):
    history = db.get_messages(chat_id)
    if not history:
        raise HTTPException(status_code=400, detail="No history found for this chat.")
    try:
        report = orchestrator.generate_report(history)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: int):
    db.delete_chat(chat_id)
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
