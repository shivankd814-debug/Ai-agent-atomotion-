import base64, hmac, secrets
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pathlib import Path
from .config import get_settings
from .providers import PROVIDERS, ProviderError, provider_status
from .agents import run_multi_agent
from .device import interpret_command, dispatch_device_command
from .store import init_db, save_task, recent_tasks, take_device_job, finish_device_job

BASE = Path(__file__).resolve().parent.parent
app = FastAPI(title="SHIVANK AI", version="0.2.0", description="Voice-first mobile + desktop personal AI operator")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

@app.middleware("http")
async def optional_basic_auth(request: Request, call_next):
    password = get_settings().app_password
    if password and request.url.path not in {"/api/health"} and not request.url.path.startswith("/api/device/"):
        auth = request.headers.get("authorization", "")
        valid = False
        if auth.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth.split(" ", 1)[1]).decode()
                _, supplied = decoded.split(":", 1)
                valid = hmac.compare_digest(supplied, password)
            except Exception:
                valid = False
        if not valid:
            return JSONResponse({"detail": "Authentication required"}, status_code=401, headers={"WWW-Authenticate": 'Basic realm="SHIVANK AI"'})
    return await call_next(request)

@app.on_event("startup")
async def startup():
    init_db()

class RunRequest(BaseModel):
    task: str = Field(min_length=3, max_length=6000)
    provider: str = Field(default="auto")

class CommandRequest(BaseModel):
    command: str = Field(min_length=2, max_length=1000)
    target: str = Field(default="this_device")

class JobResult(BaseModel):
    result: str = Field(default="completed", max_length=1000)

@app.get("/")
async def home():
    return FileResponse(BASE / "static" / "index.html")

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": get_settings().app_name, "owner": get_settings().owner_name, "version": app.version}

@app.get("/api/config")
async def config():
    return {"owner": get_settings().owner_name, "providers": provider_status(), "security": {"password_protected": bool(get_settings().app_password), "desktop_agent_paired": bool(get_settings().device_agent_token)}}

@app.get("/api/tasks")
async def tasks():
    return {"tasks": recent_tasks()}

@app.post("/api/command")
async def command(req: CommandRequest):
    if req.target not in {"this_device", "pc", "both"}:
        raise HTTPException(400, "target must be this_device, pc, or both")
    action = interpret_command(req.command, req.target)
    if not action:
        return {"handled": False, "message": "No direct device action matched. Send this as an AI task instead."}
    if action["kind"] == "media" and req.target == "this_device":
        return {"handled": True, "message": "This browser cannot reliably control native media keys. Choose PC to send it to the paired desktop companion.", "requires_pc": True}
    if req.target in {"pc", "both"}:
        if not get_settings().device_agent_token:
            raise HTTPException(503, "Desktop companion is not configured. Set DEVICE_AGENT_TOKEN on the server and PC, then restart.")
    return {"handled": True, **dispatch_device_command(action)}

@app.get("/api/device/next")
async def device_next(x_device_token: str = Header(default="")):
    token = get_settings().device_agent_token
    if not token or not hmac.compare_digest(token, x_device_token):
        raise HTTPException(401, "Invalid device pairing token")
    return {"job": take_device_job()}

@app.post("/api/device/{job_id}/result")
async def device_result(job_id: int, req: JobResult, x_device_token: str = Header(default="")):
    token = get_settings().device_agent_token
    if not token or not hmac.compare_digest(token, x_device_token):
        raise HTTPException(401, "Invalid device pairing token")
    finish_device_job(job_id, req.result)
    return {"ok": True}

@app.post("/api/run")
async def run(req: RunRequest):
    task = req.task.strip()
    if len(task) > get_settings().max_task_chars:
        raise HTTPException(413, "Task is too long")
    provider = req.provider
    if provider not in PROVIDERS and provider != "auto":
        raise HTTPException(400, "Provider must be auto, gemini, groq, or openrouter")
    order = [provider] if provider != "auto" else ["gemini", "groq", "openrouter"]
    configured = provider_status()
    order = [p for p in order if configured[p]["configured"]]
    if not order:
        raise HTTPException(503, "No AI provider configured. Add at least one key to server environment secrets.")
    errors = []
    for selected in order:
        try:
            result, trace = await run_multi_agent(task, selected)
            if provider == "auto" and selected != "gemini":
                trace.insert(0, {"agent": "Provider Fallback", "status": "completed", "output": f"Used {selected} after earlier provider was unavailable or failed."})
            task_id = save_task(task, selected, "completed", result, trace)
            return {"id": task_id, "status": "completed", "provider_used": selected, "result": result, "trace": trace}
        except ProviderError as exc:
            errors.append(f"{selected}: {str(exc)[:160]}")
            if provider != "auto":
                break
    save_task(task, provider, "failed", "; ".join(errors), [])
    raise HTTPException(502, "All selected AI providers failed: " + "; ".join(errors))
