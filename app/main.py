from fastapi import FastAPI, Request, Depends
from pydantic import BaseModel
from app.conversation import ConversationState
from app.schemas import SCHEMAS
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uuid
import os

app = FastAPI()

ACCESS_PASSWORD = "Secret_Password"
app.mount("/static", StaticFiles(directory="static"), name="static")

user_sessions = {}


@app.middleware("http")
async def assign_session(request: Request, call_next):
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    request.state.session_id = session_id
    response = await call_next(request)
    response.set_cookie("session_id", session_id)
    return response


def get_current_user():
    return "guest"

@app.get("/chat_ui", response_class=HTMLResponse)
async def serve_chat_ui(user: str = Depends(get_current_user)):
    with open("static/index.html") as f:
        return HTMLResponse(f.read())

@app.get("/", response_class=HTMLResponse)
async def serve_landing():
    with open("static/landingpage.html") as f:
        return HTMLResponse(f.read())


class Message(BaseModel):
    text: str


@app.post("/check_password")
async def check_password(request: Request):
    data = await request.json()
    return {"valid": data.get("password") == ACCESS_PASSWORD}


@app.post("/chat")
async def chat(request: Request, msg: Message):
    session_id = request.state.session_id
    if session_id not in user_sessions:
        user_sessions[session_id] = ConversationState()
    state = user_sessions[session_id]

    if state.state == "doc_selection" and state.active_schema:
        return {"response": state.confirm_document_selection(msg.text)}
    return {"response": state.handle_user_message(msg.text)}


@app.get("/download")
async def download(file: str):
    if os.path.exists(file):
        return FileResponse(file, filename=os.path.basename(file))
    return {"error": "File not found"}


@app.post("/reset")
async def reset(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id in user_sessions:
        user_sessions[session_id].reset()
    return {"status": "ok"}


@app.get("/progress")
async def progress(request: Request):
    session_id = request.cookies.get("session_id")
    state = user_sessions.get(session_id)

    if not state:
        return {
            "schema_selected": False,
            "completed": 0,
            "total": 0,
            "fields": []
        }

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
        if "name" not in field or "question" not in field:
            continue

        if "depends_on" in field and not state.evaluate_condition(field["depends_on"], state.slots):
            continue

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
