#.\venv\Scripts\Activate.ps1

import os
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI(title=os.getenv('APP_NAME', 'DraftEDI'))


@app.get("/info")
def info():
    return {
        "env": os.getenv("ENV", "unknown"),
        "app_name": os.getenv("APP_NAME", "DraftEDI"),
    }

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def root():
    return {"status": "DraftEDI API is live"}