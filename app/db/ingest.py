from app.db.conn import connect

def create_edi_file(file_dict):
    """
    file_dict expects:
      partner_id, interchange_id, processed_at, filename, file_hash, raw_bytes (bytes),
      parse_status, parse_error, processing_state, source
    """
    fields = (
        file_dict.get("partner_id"),
        file_dict.get("interchange_id"),
        file_dict.get("processed_at"),
        file_dict.get("filename"),
        file_dict.get("file_hash"),
        file_dict.get("raw_bytes"),
        file_dict.get("parse_status"),
        file_dict.get("parse_error"),
        file_dict.get("processing_state"),
        file_dict.get("source"),
    )

    with connect() as conn:
        cursor = conn.cursor()


        cursor.execute("""
            INSERT INTO edi_files
                (partner_id, interchange_id, processed_at, filename, file_hash, raw_bytes,
                    parse_status, parse_error, processing_state, source)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, fields)

        file_id = cursor.lastrowid
        file_dict["file_id"] = file_id

        conn.commit()

    return file_dict

def create_edi_interchange(interchange_dict):
    fields = (
        interchange_dict.get("file_id"),
        interchange_dict.get("partner_id"),
        interchange_dict.get("interchange_id"),

        interchange_dict.get("isa_control_number"),
        interchange_dict.get("isa_sender_qualifier"),
        interchange_dict.get("isa_sender_id"),
        interchange_dict.get("isa_receiver_qualifier"),
        interchange_dict.get("isa_receiver_id"),
        interchange_dict.get("isa_date"),
        interchange_dict.get("isa_time"),
        interchange_dict.get("usage_indicator"),
        interchange_dict.get("version"),

        interchange_dict.get("element_sep") or "*",
        interchange_dict.get("component_sep"),
        interchange_dict.get("segment_term") or "~",
        interchange_dict.get("repetition_sep"),
        interchange_dict.get("raw_isa"),
    )

    with connect() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO edi_interchanges
                (file_id, partner_id, interchange_id,
                isa_control_number, isa_sender_qualifier, isa_sender_id, isa_receiver_qualifier, isa_receiver_id,
                isa_date, isa_time, usage_indicator, version,
                element_sep, component_sep, segment_term, repetition_sep, raw_isa)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, fields)

        edi_interchange_id = cursor.lastrowid
        interchange_dict["edi_interchange_id"] = edi_interchange_id

        conn.commit()

    return interchange_dict

def create_functional_group(group_dict):
    fields = (
        group_dict.get("edi_interchange_id"),
        group_dict.get("functional_id_code"),
        group_dict.get("gs_sender_id"),
        group_dict.get("gs_receiver_id"),
        group_dict.get("group_control_number"),
        group_dict.get("x12_release"),
        group_dict.get("raw_gs_segment"),
    )

    with connect() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO edi_functional_groups
                (edi_interchange_id, functional_id_code, gs_sender_id, gs_receiver_id,
                group_control_number, x12_release, raw_gs_segment)
            VALUES
                (?, ?, ?, ?, ?, ?, ?)
        """, fields)

        group_id = cursor.lastrowid
        group_dict["group_id"] = group_id

        conn.commit()

    return group_dict

def create_transaction(tx_dict):
    fields = (
        tx_dict.get("group_id"),
        tx_dict.get("transaction_set_id"),
        tx_dict.get("control_number"),
        tx_dict.get("implementation_version"),
        tx_dict.get("segment_count_reported"),
        tx_dict.get("raw_st_segment"),
        tx_dict.get("raw_se_segment"),
        tx_dict.get("ack_status"),
    )

    with connect() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO edi_transactions
                (group_id, transaction_set_id, control_number, implementation_version,
                segment_count_reported, raw_st_segment, raw_se_segment, ack_status)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?)
        """, fields)

        transaction_id = cursor.lastrowid
        tx_dict["transaction_id"] = transaction_id

        conn.commit()

    return tx_dict

def create_segment(segment_dict):
    fields = (
        segment_dict.get("transaction_id"),
        segment_dict.get("position"),
        segment_dict.get("segment_id"),
        segment_dict.get("loop_path"),
        segment_dict.get("raw_segment"),
    )

    with connect() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO edi_segments
                (transaction_id, position, segment_id, loop_path, raw_segment)
            VALUES
                (?, ?, ?, ?, ?)
            """, fields
        )

        segment_id = cursor.lastrowid
        segment_dict["segment_row_id"] = segment_id

        conn.commit()

    return segment_dict

def create_element(element_dict):
    fields = (
        element_dict.get("segment_row_id"),
        element_dict.get("element_pos"),
        element_dict.get("is_composite"),
        element_dict.get("value_text"),
        element_dict.get("present"),
        element_dict.get("repetition_index"),
    )

    with connect() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO edi_elements
                (segment_row_id, element_pos, is_composite, value_text, present, repetition_index)
            VALUES
                (?, ?, ?, ?, ?, ?)
            """,
            fields,
        )

        element_id = cursor.lastrowid
        element_dict["element_row_id"] = element_id

        conn.commit()

    return element_dict

def create_component(component_dict):
    fields = (
        component_dict.get("element_row_id"),
        component_dict.get("componennt_pos"),
        component_dict.get("value_text"),
    )

    with connect() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO edi_components
                (element_row_id, component_pos, value_text)
            VALUES
                (?, ?, ?)
            """,
            fields,
        )

        conn.commit()

    return component_dict
