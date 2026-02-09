from fastapi import APIRouter

from app.db.partners import get_partner
router = APIRouter(prefix="/partners", tags=["partners"])

@router.get("/{partner_id}",)
def list_partners(partner_id):
    return get_partner(partner_id)