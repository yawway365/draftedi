#.\venv\Scripts\Activate.ps1

import os
import time
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, Header, HTTPException, Response, status

load_dotenv()

START_TIME = time.time()

def env(key, default=""):
    v = os.getenv(key)
    return v if v is not None else default

def require_api_key(x_api_key=Header(default=None)):
    expected = env("API_KEY", "")
    if not expected:
        # Fail closed if misconfigured
        raise HTTPException(status_code=500, detail="API key not configured on server")

    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")

app = FastAPI(title=os.getenv('APP_NAME', 'DraftEDI'))

@app.get("/health")
def health():
    # Liveness: app process is up
    return {"ok": True}

@app.get("/ready")
def ready(response: Response):
    # Later: add real checks (DB, external services, etc.)
    is_ready = True

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"ready": False}

    return {"ready": True}

@app.get("/version")
def version():
    return {
        "app_name": env("APP_NAME", "DraftEDI"),
        "env": env("ENV", "unknown"),
        "app_version": env("APP_VERSION", "unknown"),
        "git_sha": env("GIT_SHA", "unknown"),
    }

@app.get("/info")
def info():
    return {
        "env": env("ENV", "unknown"),
        "app_name": env("APP_NAME", "DraftEDI"),
        "uptime_seconds": int(time.time() - START_TIME),
    }

@app.get("/metrics")
def metrics():
    return {
        "uptime_seconds": int(time.time() - START_TIME),
        "env": env("ENV", "unknown"),
        "version": env("APP_VERSION", "unknown"),
    }

@app.get("/")
def root():
    return {"status": "DraftEDI API is live"}


# ---- Protected router (everything in here requires x-api-key) ----
protected = APIRouter(prefix="/api", dependencies=[require_api_key])

@protected.get("/ping")
def ping():
    return {"pong": True}

app.include_router(protected)