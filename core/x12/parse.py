import hashlib
import os
import sqlite3
from datetime import datetime, timezone

from app.db.ingest import insert_segment_with_elements, create_edi_file, create_transaction, lookup_trading_partner_and_interchange, create_edi_interchange, create_functional_group, update_transaction_se_fields, update_edi_file_status


TRADING_PARTNERS_DB = "trading_partners.db"


# -------------------------
# Separator detection
# -------------------------
def parse_interchange(x12_text: str):
    """
    Detect element/component/repetition separators + segment terminator from the ISA header.
    Kind of have to do this first to be able to parse any other segmet. It's consistently 106 chars and that should never change

    - element_sep is the 4th character (after "ISA")
    - segment terminator is typically the char right before the next "GS{element_sep}" token
      (works well for real-world files, including your sample.edi)
    """
    if not x12_text.startswith("ISA"):
        raise ValueError("File does not start with ISA segment")

    if len(x12_text) < 106:
        raise ValueError("File does not contain a full ISA segment")

    # ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *231117*0041*^*00403*000000001*0*T*>~
    element_sep = x12_text[3]
    segment_term = x12_text[105]
    raw_isa = x12_text[0:106]
    isa_parts = raw_isa.split(element_sep)

    # ISA has 16 elements (plus 'ISA' tag at index 0 => total len 17)
    # If shorter, still attempt best-effort
    repetition_sep = isa_parts[11] if len(isa_parts) > 11 else None  # ISA11 (5010 repetition separator)
    component_sep = isa_parts[16][0] if len(isa_parts) > 16 else None   # ISA16

    # normalize blanks
    repetition_sep = repetition_sep if repetition_sep else None
    component_sep = component_sep if component_sep else None

    return {
        "element_sep": element_sep,
        "segment_term": segment_term,
        "repetition_sep": repetition_sep,
        "component_sep": component_sep,
        "raw_isa": raw_isa,
        "isa_parts": isa_parts,
    }


# -------------------------
# Main parse + populate
# -------------------------
def parse_edi_file(raw_bytes, source="manual upload"):

    # decode best-effort; EDI is usually ASCII, but utf-8 decode works for most
    x12_text = raw_bytes.decode("utf-8", errors="replace")

    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    # filename = os.path.basename(file_path)
    filename = ''
    try:
        filename = raw_bytes.filename
    except Exception:
        filename = 'raw text'

    processed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    
    

    sep = parse_interchange(x12_text)
    element_sep = sep["element_sep"]
    segment_term = sep["segment_term"]
    repetition_sep = sep["repetition_sep"]
    component_sep = sep["component_sep"]
    isa_parts = sep["isa_parts"]
    raw_isa = sep["raw_isa"]

    # Parse ISA fields (index names based on standard positions)
    # NOTE: after split: ['ISA', ISA01, ISA02, ..., ISA16]
    isa_sender_qual = isa_parts[5] if len(isa_parts) > 5 else None
    isa_sender_id = isa_parts[6] if len(isa_parts) > 6 else None
    isa_receiver_qual = isa_parts[7] if len(isa_parts) > 7 else None
    isa_receiver_id = isa_parts[8] if len(isa_parts) > 8 else None
    isa_date = isa_parts[9] if len(isa_parts) > 9 else None
    isa_time = isa_parts[10] if len(isa_parts) > 10 else None
    isa_control = isa_parts[13] if len(isa_parts) > 13 else None
    usage_indicator = isa_parts[15] if len(isa_parts) > 15 else None
    version = isa_parts[12] if len(isa_parts) > 12 else None
    
    # Split into segments (trim whitespace/newlines around segments)
    segments = [s.strip() for s in x12_text.split(segment_term)]
    segments = [s for s in segments if s]  # drop empties

    edi_file_dict = {
        "partner_id": None,
        "interchange_id": None,
        "processed_at": processed_at,
        "filename": filename,
        "file_hash": sha256,
        "raw_bytes": raw_bytes,
        "parse_status": "new",
        "parse_error": None,
        "processing_state": "new",
        "source": source,
    }

    db_records = {
        'edi_file_dict': edi_file_dict,
        'interchange_dict': {},
        'group_dict': {},
        'transaction_dict': {},
        'segments': [],
    }

    current_group_id = None
    current_tx_id = None
    current_tx_pos = 0
    for seg in segments:
        parts = seg.split(element_sep)
        seg_id = parts[0].strip() if parts else ""
        seg_elements = parts[1:] if len(parts) > 1 else []

        if seg_id == "ISA":
            db_records['interchange_dict'] = {
                "file_id": None,
                "partner_id": None,
                "interchange_id": None,
                "isa_control_number": isa_control,
                "isa_sender_qualifier": isa_sender_qual,
                "isa_sender_id": isa_sender_id,
                "isa_receiver_qualifier": isa_receiver_qual,
                "isa_receiver_id": isa_receiver_id,
                "isa_date": isa_date,
                "isa_time": isa_time,
                "usage_indicator": usage_indicator,
                "version": version,
                "element_sep": element_sep,
                "component_sep": component_sep,
                "segment_term": segment_term,
                "repetition_sep": repetition_sep,
                "raw_isa": raw_isa,
            }
            continue

        if seg_id == "GS":
            # GS*PO*SENDERGS*RECEIVERGS*20231117*004114*000000001*X*004030
            functional_id_code = seg_elements[0] if len(seg_elements) > 0 else None
            gs_sender_id = seg_elements[1] if len(seg_elements) > 1 else None
            gs_receiver_id = seg_elements[2] if len(seg_elements) > 2 else None
            group_control_number = seg_elements[5] if len(seg_elements) > 5 else None
            x12_release = seg_elements[7] if len(seg_elements) > 7 else None

            current_group_id = functional_id_code

            db_records['group_dict'] = {
                "edi_interchange_id": None,
                "functional_id_code": functional_id_code,
                "gs_sender_id": gs_sender_id,
                "gs_receiver_id": gs_receiver_id,
                "group_control_number": group_control_number,
                "x12_release": x12_release,
                "raw_gs_segment": seg,
            }
            continue

        if seg_id == "ST":
            # ST*850*01403001*...
            if current_group_id is None:
                raise ValueError("Encountered ST before GS")

            transaction_set_id = seg_elements[0] if len(seg_elements) > 0 else None
            control_number = seg_elements[1] if len(seg_elements) > 1 else None
            impl_version = seg_elements[2] if len(seg_elements) > 2 else None

            current_tx_id = transaction_set_id
            
            db_records['transaction_dict'] = {
                "group_id": None,
                "transaction_set_id": transaction_set_id,
                "control_number": control_number,
                "implementation_version": impl_version,
                "segment_count_reported": None,
                "raw_st_segment": seg,
                "raw_se_segment": None,
                "ack_status": "none",
            }
            
            current_tx_pos = 0

        if seg_id == "SE":
            # SE*21*01403001
            if current_tx_id is None:
                raise ValueError("Encountered SE but no active transaction")

            seg_count = None
            if len(seg_elements) > 0 and seg_elements[0].isdigit():
                seg_count = int(seg_elements[0])

            # store SE segment into segment table
            current_tx_pos += 1

            # update transaction with SE info
            db_records['transaction_dict'] = {
                "segment_count_reported": seg_count,
                "raw_se_segment": seg,
            }

            # close tx
            current_tx_id = None
            current_tx_pos = 0
            continue

        if seg_id == "GE":
            current_group_id = None
            continue

        if seg_id == "IEA":
            # done with interchange
            continue

        
        # Normal business segments: only store if inside a transaction
        if current_tx_id is not None:
            current_tx_pos += 1

            segment_dict = {
                'transaction_id': current_tx_id,
                'position': current_tx_pos,
                'segment_id': seg_id,
                'loop_path': None,
                'raw_segment': seg,
                'elements': []
            }

            for element_pos, val in enumerate(seg_elements, start=1):
                # val can be "" (blank) and is still "present"
                if val is None:
                    val = ""
                
                reps = [val]
                if repetition_sep and repetition_sep in val:
                    reps = val.split(repetition_sep)

                element_dict = {
                    'element_pos': element_pos,
                    'is_composite': None,
                    'value_text': None,
                    'present': 1,
                    'repetition_index': None,
                    'components': [],
                }

                for rep_index, rep_val in enumerate(reps, start=1):
                    element_dict['repetition_index'] = rep_index

                    if component_sep and component_sep in rep_val:
                        element_dict['is_composite'] = 1
                        
                        components = rep_val.split(component_sep)
                        for component_pos, cval in enumerate(components, start=1):
                            component_dict = {
                                'component_pos': component_pos,
                                'value_text': cval
                            }
                            element_dict['components'].append(component_dict)
                        
                        segment_dict['elements'].append(element_dict)

                    else:
                        element_dict['is_composite'] = 0
                        element_dict['value_text'] = rep_val
                        segment_dict['elements'].append(element_dict)

            db_records['segments'].append(segment_dict)
        else:
            # segments outside transaction (rare) => ignore for now
            pass

        return edi_file_dict

def main():
    # default to your sample file
    file_id = parse_edi_file("sample.edi")
    print(f"Parsed EDI file -> edi_files.file_id = {file_id}")


if __name__ == "__main__":
    main()