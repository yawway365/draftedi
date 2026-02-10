from app.db.transaction_sets import get_transaction_set

def build_mapping_template(version: str, transaction_set_id: str) -> dict:

    tx_set = get_transaction_set(version, transaction_set_id)

    if not tx_set:
        raise ValueError(f"Transaction set {transaction_set_id} not found in version {version}")
    
    template = {
        "transaction_set": transaction_set_id,
        "transaction_set_name": tx_set.get("transaction_set_name"),
        "version": version,
        "segments": _process_segments(tx_set.get("segments", []))
    }

    return template

def _process_segments(segments_list):
    result = []

    for item in segments_list:
        # Check if this is a nested loop (list) or a regular segment (dict)
        if isinstance(item, list):
            # This is a loop - recursively process its segments
            loop_segments = _process_segments(item)
            result.append({
                "type": "loop",
                "segments": loop_segments
            })
        elif isinstance(item, dict):
            # This is a regular segment
            segment = _build_segment_template(item)
            result.append(segment)
    
    return result

def _build_segment_template(segment_dict):

    segment_id = segment_dict.get("segment_id")

    # Filter to only mandatory or conditionally required segments
    requirement = segment_dict.get("segment_requirement", "")

    # Build basic segment structure
    segment_template = {
        "segment_id": segment_id,
        "loop_id": segment_dict.get("segment_loop_id"),
        "loop_level": segment_dict.get("segment_loop_level"),
        "area": segment_dict.get("segment_area_name"),
        "requirement": requirement,
        "max_use": segment_dict.get("segment_maximum_use"),
        "elements": []
    }

    # Add notes if present
    notes = segment_dict.get("segment_notes", [])
    if notes:
        segment_template["notes"] = [
            {
                "type": note.get("transaction_set_segment_note_type"),
                "content": note.get("transaction_set_segment_note_content")
            }
            for note in notes
        ]
    
    # Add relational conditions if present
    rel_conditions = segment_dict.get("segment_relational_conditions", [])
    if rel_conditions:
        segment_template["relational_conditions"] = [
            {
                "type": rc.get("transaction_set_segment_rc_type"),
                "elements": rc.get("transaction_set_segment_rc_elements", [])
            }
            for rc in rel_conditions
        ]
    
    # Process elements
    segment_elements = segment_dict.get("segment_elements", [])
    for element in segment_elements:
        element_template = _build_element_template(element)
        segment_template["elements"].append(element_template)

    return segment_template

def _build_element_template(element_dict):

    element_id = element_dict.get("element_id")
    requirement = element_dict.get("segment_element_requirement", "")

    element_template = {
        "pos": element_dict.get("segment_element_sequence"),
        "element_id": element_id,
        "name": element_dict.get("element_name"),
        "requirement": requirement,
        "type": element_dict.get("element_type"),
        "min_length": element_dict.get("element_min_length"),
        "max_length": element_dict.get("element_max_length"),
        "repetition_count": element_dict.get("segment_element_repetition_count"),
        "value": None,  # Placeholder for actual data
        "path": ""  # Path to data source (to be filled in during mapping)
    }

    # Add notes if present
    notes = element_dict.get("segment_element_notes", [])
    if notes:
        element_template["notes"] = [
            {
                "type": note.get("segment_element_note_type"),
                "content": note.get("segment_element_note_content")
            }
            for note in notes
        ]
    
    # Add description/definition
    definition = element_dict.get("element_definition")
    if definition:
        element_template["definition"] = definition
    
    return element_template

def build_mandatory_only_template(version, transaction_set_id):
    # Get the full template first
    full_template = build_mapping_template(version, transaction_set_id)
    
    # Filter to mandatory only
    full_template["segments"] = _filter_mandatory_segments(full_template["segments"])
    
    return full_template

def _filter_mandatory_segments(segments_list):
    result = []

    for item in segments_list:
        if isinstance(item, dict):
            if item.get("type") == "loop":
                # Recursively filter loop segments
                filtered_loop_segments = _filter_mandatory_segments(item.get("segments", []))
                if filtered_loop_segments:
                    result.append({
                        "type": "loop",
                        "segments": filtered_loop_segments
                    })
            else:
                # Regular segment - check if mandatory
                requirement = item.get("requirement", "")
                if requirement == "M":  # Mandatory
                    # Filter elements to mandatory only
                    mandatory_elements = [
                        elem for elem in item.get("elements", [])
                        if elem.get("requirement") == "M"
                    ]
                    
                    # Create a copy with only mandatory elements
                    mandatory_segment = item.copy()
                    mandatory_segment["elements"] = mandatory_elements
                    result.append(mandatory_segment)
    
    return result

def validate_template_data(template, data):
    errors = []
    
    # This is a placeholder for future validation logic
    # Would check:
    # - All mandatory segments have data
    # - All mandatory elements have values
    # - Data types match
    # - Lengths are within min/max bounds
    # - Relational conditions are satisfied
    
    return len(errors) == 0, errors