import os
import json
import logging
import datetime
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# --- CONFIGURATION ---
# The behavior changes based on this environment variable
# Options: 'ollama', 'vllm', 'mcp'
PROFILE = os.getenv("HONEYPOT_PROFILE", "generic")

LOG_FILE = "/var/log/honeypot_events.json"

# --- LOGGING SETUP ---
# specific logger to avoid capturing uvicorn's internal noise
logger = logging.getLogger("honeypot")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = FastAPI(docs_url=None, redoc_url=None) # Hide docs to look less suspicious

# --- CORE LOGGING MIDDLEWARE ---
@app.middleware("http")
async def log_attack_traffic(request: Request, call_next):
    # 1. Capture the Request Body (The "Payload")
    body_content = ""
    try:
        body_bytes = await request.body()
        if body_bytes:
            # Try to decode as UTF-8, fallback to hex if binary
            try:
                body_content = json.loads(body_bytes)
            except:
                body_content = body_bytes.decode('utf-8', errors='ignore')
    except Exception:
        body_content = "[Read Error]"

    # 2. Build the Log Entry
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "profile": PROFILE,
        "src_ip": request.client.host,
        "method": request.method,
        "path": request.url.path,
        "headers": dict(request.headers),
        "body": body_content
    }

    # 3. Save to disk (Atomic-ish write)
    logger.info(json.dumps(log_entry))

    # 4. Pass request to the specific profile handler
    response = await call_next(request)
    return response

# --- PROFILE 1: FAKE OLLAMA (Port 11434) ---
if PROFILE == "ollama":
    @app.get("/")
    async def ollama_root():
        return "Ollama is running"

    @app.get("/api/tags")
    async def list_models():
        # The Scanner checks this to verify it's a real Ollama instance
        return {
            "models": [
                {
                    "name": "llama3:latest",
                    "model": "llama3:latest",
                    "modified_at": "2025-01-20T12:00:00Z",
                    "size": 4700000000,
                    "digest": "sha256:fakehash123"
                },
                {
                    "name": "mistral:latest",
                    "model": "mistral:latest", 
                    "modified_at": "2025-01-21T10:00:00Z",
                    "size": 4100000000,
                    "digest": "sha256:fakehash456"
                }
            ]
        }

    @app.post("/api/generate")
    @app.post("/api/chat")
    async def generate_fake_response(request: Request):
        # The Validator sends a prompt here to see if the LLM works.
        # We return a valid dummy JSON to "pass" the test.
        return {
            "model": "llama3",
            "created_at": datetime.datetime.now().isoformat(),
            "response": "I am a helpful AI assistant. How can I help you today?",
            "done": True,
            "context": [1, 2, 3],
            "total_duration": 500000,
            "load_duration": 100000,
            "prompt_eval_count": 10,
            "eval_count": 10
        }

# --- PROFILE 2: FAKE vLLM / OPENAI (Port 8000) ---
elif PROFILE == "vllm":
    @app.get("/v1/models")
    @app.get("/models")
    async def list_openai_models():
        # Mimics the OpenAI/vLLM /models endpoint
        return {
            "object": "list",
            "data": [
                {
                    "id": "gpt-3.5-turbo",
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "openai"
                },
                {
                    "id": "meta-llama/Llama-2-7b-chat-hf",
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "vllm"
                }
            ]
        }

    @app.post("/v1/chat/completions")
    @app.post("/v1/completions")
    async def openai_chat(request: Request):
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": int(datetime.datetime.now().timestamp()),
            "model": "gpt-3.5-turbo",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! I am a vLLM instance. I am ready to help."
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 7,
                "total_tokens": 12
            }
        }

# --- PROFILE 3: FAKE MCP (Port 3000/8080) ---
elif PROFILE == "mcp":
    # Catches Model Context Protocol probes
    # MCP is often JSON-RPC or SSE. We accept everything to log the payload.
    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def catch_all_mcp(path_name: str, request: Request):
        # We return a generic 200 OK JSON to encourage them to send more
        return JSONResponse(
            status_code=200, 
            content={"jsonrpc": "2.0", "result": "ok", "id": 1}
        )
