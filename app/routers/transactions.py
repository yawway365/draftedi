from fastapi import APIRouter, Query, UploadFile, File, HTTPException, Request

from db.transactions import get_transactions
router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("",)
def list_transactions(
    limit=Query(50, ge=1, le=500),
    offset=Query(0, ge=0),
    file_id=None,
    transaction_set_id=None,
    ack_status= None,
):
    return get_transactions(limit, offset, file_id, transaction_set_id, ack_status)