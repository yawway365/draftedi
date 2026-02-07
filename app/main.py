from fastapi import FastAPI

app = FastAPI(title="DraftEDI")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def root():
    return {"status": "DraftEDI API is live"}