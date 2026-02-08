from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/x12", tags=["x12"])

class X12ParseResponse(BaseModel):
    interchange: dict[str, Any] | None = None
    functional_group: dict[str, Any] | None = None
    transaction_set: dict[str, Any] | None = None
    segment_count: int
    segments_preview: list[str] = []
    errors: list[str] = []

def _normalize_x12(text: str) -> str:
    # Keep it simple: strip BOM/whitespace; don’t over-normalize yet.
    return text.strip("\ufeff").strip()

@router.post("/parse", response_model=X12ParseResponse)
async def parse_x12(request: Request, file: UploadFile | None = File(default=None)):
    """
    Accepts either:
      - text/plain body containing raw X12
      - multipart/form-data with a 'file'
    """
    raw: str | None = None

    if file is not None:
        data = await file.read()
        try:
            raw = data.decode("utf-8", errors="replace")
        except Exception as e:
            raise HTTPException(status_code=400, detail="Could not decode uploaded file as UTF-8.") from e
    else:
        # Accept raw body
        content_type = (request.headers.get("content-type") or "").lower()
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Empty request body. Send X12 as text/plain or upload a file.")
        raw = body.decode("utf-8", errors="replace")

        # Optional: enforce content type if you want strictness
        # if "text/plain" not in content_type:
        #     raise HTTPException(status_code=415, detail="Send as text/plain or multipart file upload.")

    x12_text = _normalize_x12(raw)

    # ---- Call your existing parser here ----
    try:
        # Example integration point (you will replace this with your real function)
        # from simple_edi.x12 import parse_interchange
        # parsed = parse_interchange(x12_text)

        parsed = fake_parse_for_now(x12_text)  # replace
    except Exception as e:
        # Don’t leak internals; return a useful error
        raise HTTPException(status_code=400, detail=f"Parse failed: {e}") from e

    # Build an MVP response
    segments = parsed.get("segments", [])
    seg_preview = ["*".join(seg) if isinstance(seg, (list, tuple)) else str(seg) for seg in segments[:20]]

    return X12ParseResponse(
        interchange=parsed.get("interchange"),
        functional_group=parsed.get("functional_group"),
        transaction_set=parsed.get("transaction_set"),
        segment_count=len(segments),
        segments_preview=seg_preview,
        errors=parsed.get("errors", []),
    )

# Temporary stub so the API runs before you wire in your real parser
def fake_parse_for_now(x12_text: str) -> dict[str, Any]:
    # Extremely naive segment split for stub only
    segs = [s for s in x12_text.split("~") if s.strip()]
    parsed_segments = [seg.strip().split("*") for seg in segs]
    return {
        "interchange": {"note": "stub"},
        "functional_group": {"note": "stub"},
        "transaction_set": {"note": "stub"},
        "segments": parsed_segments,
        "errors": [],
    }