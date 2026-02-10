from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.build_mapping_template import (
    build_mapping_template,
    build_mandatory_only_template
)
from app.db.mappings import (
    create_transaction_set_mapping,
    get_transaction_set_mapping,
    get_mappings_for_interchange_set,
    update_transaction_set_mapping,
    delete_transaction_set_mapping
)

router = APIRouter(prefix="/mappings", tags=["mappings"])

class CreateMappingRequest(BaseModel):
    interchange_set_id: int
    mapping_name: str
    version: str  # X12 version (e.g., "004010")
    transaction_set_id: str  # e.g., "810"
    mapping_version: str = "1.0"
    mandatory_only: bool = False  # If True, only include mandatory segments/elements
    sample_input_json: Optional[dict] = None
    sample_output_edi: Optional[str] = None
    is_active: int = 1


class UpdateMappingRequest(BaseModel):
    mapping_name: Optional[str] = None
    template: Optional[dict] = None
    mapping_version: Optional[str] = None
    sample_input_json: Optional[dict] = None
    sample_output_edi: Optional[str] = None
    is_active: Optional[int] = None


@router.post("/generate")
def generate_mapping_template(
    version: str,
    transaction_set_id: str,
    mandatory_only: bool = False
):
    """
    Generate a mapping template from X12 specification without saving it.
    
    Useful for previewing what the template will look like before creating a mapping.
    """
    try:
        if mandatory_only:
            template = build_mandatory_only_template(version, transaction_set_id)
        else:
            template = build_mapping_template(version, transaction_set_id)
        
        return {
            "success": True,
            "template": template
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    
@router.post("")
def create_mapping(request: CreateMappingRequest):
    """
    Create a new transaction set mapping for an interchange set.
    
    This will generate a template from the X12 specification and save it.
    """
    try:
        # Generate the template from X12 spec
        if request.mandatory_only:
            template = build_mandatory_only_template(
                request.version,
                request.transaction_set_id
            )
        else:
            template = build_mapping_template(
                request.version,
                request.transaction_set_id
            )
        
        transaction_set_map_dict = {
            "interchange_set_id": request.interchange_set_id,
            "mapping_name": request.mapping_name,
            "template_dict": template,
            "mapping_version": request.mapping_version,
            "sample_input_json": request.sample_input_json,
            "sample_output_edi": request.sample_output_edi,
            "is_active": request.is_active
        }
        # Save the mapping
        mapping = create_transaction_set_mapping(transaction_set_map_dict)
        
        return {
            "success": True,
            "mapping": mapping
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.get("/{mapping_id}")
def get_mapping(mapping_id: int):
    """
    Retrieve a specific mapping by ID.
    """
    mapping = get_transaction_set_mapping(mapping_id)
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    return mapping

@router.get("/interchange-set/{interchange_set_id}")
def get_interchange_set_mappings(interchange_set_id: int):
    """
    Get all mappings for a specific interchange set.
    """
    mappings = get_mappings_for_interchange_set(interchange_set_id)
    
    return {
        "interchange_set_id": interchange_set_id,
        "count": len(mappings),
        "mappings": mappings
    }

@router.put("/{mapping_id}")
def update_mapping(mapping_id: int, request: UpdateMappingRequest):
    """
    Update an existing mapping.
    """
    try:
        mapping = update_transaction_set_mapping(
            mapping_id=mapping_id,
            mapping_name=request.mapping_name,
            template_dict=request.template,
            mapping_version=request.mapping_version,
            sample_input_json=request.sample_input_json,
            sample_output_edi=request.sample_output_edi,
            is_active=request.is_active
        )
        
        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")
        
        return {
            "success": True,
            "mapping": mapping
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    
@router.delete("/{mapping_id}")
def delete_mapping(mapping_id: int):
    """
    Delete a mapping.
    """
    success = delete_transaction_set_mapping(mapping_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    return {
        "success": True,
        "message": f"Mapping {mapping_id} deleted"
    }