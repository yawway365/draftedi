#.\venv\Scripts\Activate.ps1

import os
import time
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

START_TIME = time.time()

def env(key: str, default: str = "") -> str:
    v = os.getenv(key)
    return v if v is not None else default

app = FastAPI(title=os.getenv('APP_NAME', 'DraftEDI'))

@app.get("/health")
def health():
    # Liveness: app process is up
    return {"ok": True}

@app.get("/ready")
def ready():
    # Readiness: later you can add checks (DB, redis, etc.)
    # For now: always ready if process is running.
    # SO check if you can connect to needed DB
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


@app.get("/")
def root():
    return {"status": "DraftEDI API is live"}