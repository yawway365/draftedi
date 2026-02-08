from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException, Request

router = APIRouter(prefix="/x12", tags=["x12"])

@router.post("/parse")
async def parse_x12(request: Request, file: UploadFile | None = File(default=None)):
    """
    Accepts either:
      - text/plain body containing raw X12
      - multipart/form-data with a 'file'
    """
    data: bytes
    
    if file is not None:
        data = open(file, "rb").read()
    else:
        # Accept raw body
        content_type = (request.headers.get("content-type") or "").lower()
        if "text/plain" not in content_type:
            raise HTTPException(status_code=415, detail="Send as text/plain or multipart file upload.")
        
        data = await request.body()
        if not data:
            raise HTTPException(status_code=400, detail="Empty request body. Send X12 as text/plain or upload a file.")
                
    # ---- Call your existing parser here ----
    try:
        from core.x12.parse import parse_edi_file
        parsed = parse_edi_file(data)
       
    except Exception as e:
        # Don’t leak internals; return a useful error
        raise HTTPException(status_code=400, detail=f"Parse failed: {e}") from e

    # Build an MVP response
    info = parsed.get("info", [])
    return {
        # to be implemented once databases are created and parse_edi_file() can write to them.
    }
