import json
from app.db.conn import connect

def create_transaction_set_mapping(transaction_set_map_dict):
    """
    transaction_set_map expects:
        interchange_set_id: FK to interchange_sets table
        mapping_name: Descriptive name for this mapping
        template_dict: The mapping template as a dict (will be JSON serialized)
        mapping_version: Version of this mapping (default "1.0")
        sample_input_json: Optional sample input data for testing
        sample_output_edi: Optional sample EDI output for testing
        is_active: Whether this mapping is active (default 1)
    """

    template_json = json.dumps(transaction_set_map_dict.get("template_dict", {}))
    sample_input = json.dumps(transaction_set_map_dict.get("sample_input_json", {})) if transaction_set_map_dict.get("sample_input_json") else None

    fields = (
        transaction_set_map_dict.get("interchange_set_id"),
        transaction_set_map_dict.get("mapping_name"),
        template_json,
        transaction_set_map_dict.get("mapping_version", "1.0"),
        sample_input,
        transaction_set_map_dict.get("sample_output_edi"),
        transaction_set_map_dict.get("is_active", 1),
    )

    with connect() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO transaction_set_mappings
                (interchange_set_id, mapping_name, mapping_version, 
                 template_json, sample_input_json, sample_output_edi, is_active)
            VALUES
                (?, ?, ?, ?, ?, ?, ?)
        """, fields)
        
        mapping_id = cursor.lastrowid
        transaction_set_map_dict["mapping_id"] = mapping_id

        conn.commit()

    return transaction_set_map_dict

def get_transaction_set_mapping(mapping_id):
    with connect() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                mapping_id,
                interchange_set_id,
                mapping_name,
                mapping_version,
                template_json,
                sample_input_json,
                sample_output_edi,
                is_active,
                created_at,
                updated_at
            FROM transaction_set_mappings
            WHERE mapping_id = ?
        """, (mapping_id,))
        
        row = cursor.fetchone()
    
    if not row:
        return None
    
    mapping = dict(row)
    
    # Parse JSON fields
    mapping["template"] = json.loads(mapping.pop("template_json"))
    
    if mapping.get("sample_input_json"):
        mapping["sample_input"] = json.loads(mapping.pop("sample_input_json"))
    else:
        mapping.pop("sample_input_json", None)
    
    return mapping

def get_mappings_for_interchange_set(interchange_set_id):
    with connect() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                mapping_id,
                interchange_set_id,
                mapping_name,
                mapping_version,
                template_json,
                sample_input_json,
                sample_output_edi,
                is_active,
                created_at,
                updated_at
            FROM transaction_set_mappings
            WHERE interchange_set_id = ?
            ORDER BY created_at DESC
        """, (interchange_set_id,))
        
        rows = cursor.fetchall()
    
    mappings = []
    for row in rows:
        mapping = dict(row)
        mapping["template"] = json.loads(mapping.pop("template_json"))
        
        if mapping.get("sample_input_json"):
            mapping["sample_input"] = json.loads(mapping.pop("sample_input_json"))
        else:
            mapping.pop("sample_input_json", None)
        
        mappings.append(mapping)
    
    return mappings

def update_transaction_set_mapping(
    mapping_id,
    mapping_name = None,
    template_dict = None,
    mapping_version = None,
    sample_input_json = None,
    sample_output_edi = None,
    is_active = None
):
    # Build dynamic UPDATE query
    updates = []
    values = []
    
    if mapping_name is not None:
        updates.append("mapping_name = ?")
        values.append(mapping_name)
    
    if template_dict is not None:
        updates.append("template_json = ?")
        values.append(json.dumps(template_dict))
    
    if mapping_version is not None:
        updates.append("mapping_version = ?")
        values.append(mapping_version)
    
    if sample_input_json is not None:
        updates.append("sample_input_json = ?")
        values.append(json.dumps(sample_input_json))
    
    if sample_output_edi is not None:
        updates.append("sample_output_edi = ?")
        values.append(sample_output_edi)
    
    if is_active is not None:
        updates.append("is_active = ?")
        values.append(is_active)
    
    if not updates:
        # Nothing to update
        return get_transaction_set_mapping(mapping_id)
    
    # Add updated_at timestamp
    updates.append("updated_at = CURRENT_TIMESTAMP")
    
    # Add mapping_id to values for WHERE clause
    values.append(mapping_id)
    
    sql = f"""
        UPDATE transaction_set_mappings
        SET {', '.join(updates)}
        WHERE mapping_id = ?
    """
    
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, values)
        conn.commit()
    
    return get_transaction_set_mapping(mapping_id)

def delete_transaction_set_mapping(mapping_id):
    with connect() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM transaction_set_mappings
            WHERE mapping_id = ?
        """, (mapping_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
    
    return deleted
