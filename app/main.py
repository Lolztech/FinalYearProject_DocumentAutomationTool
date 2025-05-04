from fastapi import FastAPI, Depends
from pydantic import BaseModel
from app.conversation import ConversationState
from app.schemas import SCHEMAS
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()
state = ConversationState()

# Serve /static/ directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dummy session check — replace this with real logic if needed
def get_current_user():
    # For now, no auth: always return dummy user
    return "guest"

# Serve the chatbot frontend
@app.get("/chat_ui", response_class=HTMLResponse)
async def serve_chat_ui(user: str = Depends(get_current_user)):
    with open("static/index.html") as f:
        return HTMLResponse(f.read())

# Serve the landing page
@app.get("/", response_class=HTMLResponse)
async def serve_landing():
    with open("static/landingpage.html") as f:
        return HTMLResponse(f.read())

# Message input format
class Message(BaseModel):
    text: str

# Chat handler
@app.post("/chat")
async def chat(msg: Message):
    if state.state == "doc_selection" and state.active_schema:
        return {"response": state.confirm_document_selection(msg.text)}
    return {"response": state.handle_user_message(msg.text)}

# File download endpoint
@app.get("/download")
async def download(file: str):
    if os.path.exists(file):
        return FileResponse(file, filename=os.path.basename(file))
    return {"error": "File not found"}

# Reset all
@app.post("/reset")
async def reset():
    global state
    state.reset()
    return {"status": "ok"}



# Track user progress through document
@app.get("/progress")
async def progress():
    schema = state.active_schema
    slots = state.slots
    fields = []

    if not schema or schema not in SCHEMAS:
        return {
            "schema_selected": False,
            "completed": 0,
            "total": 0,
            "fields": []
        }

    schema_fields = SCHEMAS[schema]["fields"]
    current = state._current_field()
    current_name = current.get("name") if current else None

    completed = 0
    current_section = None

    for field in schema_fields:
        # Skip non-question fields
        if "name" not in field or "question" not in field:
            continue

        if "depends_on" in field and not state.evaluate_condition(field["depends_on"], state.slots):
            continue

        # Insert section divider if entering a new section
        if field.get("section") != current_section:
            fields.append({
                "type": "section",
                "label": field["section"]
            })
            current_section = field["section"]

        status = (
            "done" if field["name"] in slots else
            "current" if field["name"] == current_name else
            "pending"
        )

        if status == "done":
            completed += 1

        fields.append({
            "type": "field",
            "name": field["name"],
            "status": status
        })

    return {
        "schema_selected": True,
        "completed": completed,
        "total": sum(1 for f in schema_fields if "name" in f and "question" in f),
        "fields": fields
    }
