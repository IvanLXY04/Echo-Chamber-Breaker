import os
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List
from app.orchestrator import orchestrator
from app.policy_server import policy_server
import app.db as db

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: int):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)

    def disconnect(self, websocket: WebSocket, chat_id: int):
        if chat_id in self.active_connections:
            self.active_connections[chat_id].remove(websocket)

    async def broadcast(self, message: dict, chat_id: int):
        if chat_id in self.active_connections:
            for connection in self.active_connections[chat_id]:
                await connection.send_json(message)

manager = ConnectionManager()

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
    format: str = "Free Debate"

class UpdateChatNameRequest(BaseModel):
    name: str

@app.post("/chats")
async def create_chat(req: CreateChatRequest):
    chat_name = f"Debate: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    chat_id = db.create_chat(req.email, chat_name, req.persona, req.difficulty, req.format)
    return {"id": chat_id, "name": chat_name, "persona": req.persona, "difficulty": req.difficulty, "format": req.format}

@app.get("/chats")
async def get_chats(email: str):
    chats = db.get_chats_by_email(email)
    return chats

@app.get("/chats/{chat_id}")
async def get_chat_history(chat_id: int):
    messages = db.get_messages(chat_id)
    return messages

@app.get("/users/{email}/analytics")
async def get_analytics(email: str):
    chats = db.get_chats_by_email(email)
    total_debates = len(chats)
    total_score = 0
    score_count = 0
    fallacy_counts = {}
    
    for chat in chats:
        messages = db.get_messages(chat["id"])
        for msg in messages:
            if msg.get("a2ui_payload"):
                components = msg["a2ui_payload"].get("components", [])
                for comp in components:
                    if comp.get("component") == "ProgressBar" and comp.get("id") == "score":
                        total_score += int(comp.get("value", 0))
                        score_count += 1
                    if comp.get("component") == "WarningCard" and comp.get("id") == "fallacy":
                        title = comp.get("title", "Unknown Fallacy")
                        fallacy_counts[title] = fallacy_counts.get(title, 0) + 1
                        
    average_score = round(total_score / score_count, 1) if score_count > 0 else 0
    sorted_fallacies = [{"title": k, "count": v} for k, v in sorted(fallacy_counts.items(), key=lambda item: item[1], reverse=True)]
    
    return {
        "total_debates": total_debates,
        "average_score": average_score,
        "frequent_fallacies": sorted_fallacies[:5]
    }

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

@app.websocket("/ws/chats/{chat_id}/{email}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int, email: str):
    await manager.connect(websocket, chat_id)
    try:
        while True:
            data = await websocket.receive_json()
            message_text = data.get("message")
            persona = data.get("persona", "Socratic")
            difficulty = data.get("difficulty", "Normal")
            
            # Save user message
            db.add_message(chat_id, "user", message_text)
            
            # Broadcast human message
            await manager.broadcast({
                "type": "human_message",
                "sender": email,
                "text": message_text
            }, chat_id)
            
            # Get history and process
            history = db.get_messages(chat_id)
            result = orchestrator.process_turn(message_text, persona, difficulty, history)
            
            # Save AI response
            db.add_message(chat_id, "opponent", result["opponent_response"], result.get("referee_scorecard"))
            
            # Broadcast AI response
            await manager.broadcast({
                "type": "ai_message",
                "opponent_response": result["opponent_response"],
                "referee_scorecard": result.get("referee_scorecard")
            }, chat_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
