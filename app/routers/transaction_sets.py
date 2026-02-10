from fastapi import APIRouter, HTTPException
from app.db.transaction_sets import get_transaction_set, get_all_transaction_sets
from app.services.build_mapping_template import (
    build_mapping_template,
    build_mandatory_only_template
)

router = APIRouter(prefix="/transaction-sets", tags=["transaction-sets"])

@router.get("/{version}")
def list_transaction_sets(version: str):
    """Get all transaction sets for a given X12 version"""
    try:
        return get_all_transaction_sets(version)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.get("/{version}/{transaction_set_id}")
def get_transaction_set_detail(version: str, transaction_set_id: str):
    """Get detailed information about a specific transaction set"""
    try:
        tx_set = get_transaction_set(version, transaction_set_id)
        if not tx_set:
            raise HTTPException(status_code=404, detail="Transaction set not found")
        return tx_set
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.get("/{version}/{transaction_set_id}/template")
def get_mapping_template(version: str, transaction_set_id: str, mandatory_only: bool = False):
    """Generate a mapping template for a transaction set"""
    try:
        if mandatory_only:
            template = build_mandatory_only_template(version, transaction_set_id)
        else:
            template = build_mapping_template(version, transaction_set_id)
        
        return {
            "version": version,
            "transaction_set_id": transaction_set_id,
            "mandatory_only": mandatory_only,
            "template": template
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e