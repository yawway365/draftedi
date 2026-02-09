from fastapi import APIRouter

from app.db.transactions import get_transactions
router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("",)
def list_transactions(
    file_id=None,
    transaction_set_id=None,
    ack_status= None,
):
    return get_transactions(file_id, transaction_set_id, ack_status)