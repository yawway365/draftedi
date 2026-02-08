import sqlite3
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
        conn.close()

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

def lookup_trading_partner_and_interchange(isa_sender_id, isa_receiver_id, sender_qual, receiver_qual, gs_sender_id, gs_receiver_id):
    """
    Best-effort mapping to your configured interchanges in trading_partners.db.

    Matches on:
      interchanges.isa_sender_id == ISA06 and interchanges.isa_receiver_id == ISA08

    Returns: (partner_id, interchange_id) or (None, None)
    """
    def _clean(v):
        return (v or "").strip()
    
    isa_sender_id   = _clean(isa_sender_id)
    isa_receiver_id = _clean(isa_receiver_id)
    sender_qual     = _clean(sender_qual)
    receiver_qual   = _clean(receiver_qual)
    gs_sender_id    = _clean(gs_sender_id)
    gs_receiver_id  = _clean(gs_receiver_id)

    try:
        with connect() as conn:
            cursor = conn.cursor()

            sql = """
                SELECT
                    i.interchange_id,
                    i.interchange_partner_id AS partner_id
                FROM interchanges i
                WHERE i.isa_sender_id = ?
                AND i.isa_receiver_id = ?
                AND i.isa_sender_qualifier = ?
                AND i.isa_receiver_qualifier = ?
                AND i.gs_sender_id = ?
                AND i.gs_receiver_id = ?
                LIMIT 1
                """
            

            cursor.execute(
                sql,
                (isa_sender_id, isa_receiver_id, sender_qual, receiver_qual, gs_sender_id, gs_receiver_id),
            )

            row = cursor.fetchone()

            print(row)

            if not row:
                return None, None

        return int(row["partner_id"]), int(row["interchange_id"])
    except Exception as e:
        print(e)
        return None, None

def insert_segment_with_elements(
    transaction_id: int,
    position: int,
    segment_id: str,
    raw_segment: str,
    element_values,
    component_sep=None,
    repetition_sep=None,
    loop_path=None,
):
    """
    Insert into edi_segments, edi_elements, edi_components.

    - element_values is the list after the segment id: e.g. for "BEG*00*SA*..."
    - repetitions: split by repetition_sep => multiple edi_elements rows with same element_pos,
      different repetition_index (1..n)
    - composites: split by component_sep => insert element is_composite=1 + components rows
    """
    with connect() as conn:
        cur = conn.cursor()

        # insert segment row
        cur.execute(
            """
            INSERT INTO edi_segments
                (transaction_id, position, segment_id, loop_path, raw_segment)
            VALUES
                (?, ?, ?, ?, ?)
            """,
            (transaction_id, position, segment_id, loop_path, raw_segment),
        )
        segment_row_id = cur.lastrowid

        # elements are 1-based position
        for element_pos, val in enumerate(element_values, start=1):
            # val can be "" (blank) and is still "present"
            if val is None:
                val = ""

            reps = [val]
            if repetition_sep and repetition_sep in val:
                reps = val.split(repetition_sep)

            for rep_index, rep_val in enumerate(reps, start=1):
                # composite?
                if component_sep and component_sep in rep_val:
                    cur.execute(
                        """
                        INSERT INTO edi_elements
                            (segment_row_id, element_pos, is_composite, value_text, present, repetition_index)
                        VALUES
                            (?, ?, 1, NULL, 1, ?)
                        """,
                        (segment_row_id, element_pos, rep_index),
                    )
                    element_row_id = cur.lastrowid

                    components = rep_val.split(component_sep)
                    for component_pos, cval in enumerate(components, start=1):
                        cur.execute(
                            """
                            INSERT INTO edi_components
                                (element_row_id, component_pos, value_text)
                            VALUES
                                (?, ?, ?)
                            """,
                            (element_row_id, component_pos, cval),
                        )
                else:
                    cur.execute(
                        """
                        INSERT INTO edi_elements
                            (segment_row_id, element_pos, is_composite, value_text, present, repetition_index)
                        VALUES
                            (?, ?, 0, ?, 1, ?)
                        """,
                        (segment_row_id, element_pos, rep_val, rep_index),
                    )

    return segment_row_id

def update_transaction_se_fields(transaction_id: int, segment_count_reported, raw_se_segment: str):
    """
    Your db.edi_data module doesn't have an update_transaction helper, so we do a small direct update.
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE edi_transactions
            SET
                segment_count_reported = ?,
                raw_se_segment = ?
            WHERE transaction_id = ?
            """,
            (segment_count_reported, raw_se_segment, transaction_id),
        )
        conn.commit()

def update_edi_file_status(file_id, parse_status=None, parse_error=None, processing_state=None):
    fields = (
        parse_status,
        parse_error,
        processing_state,
        file_id,
    )

    with connect() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE edi_files
            SET
                parse_status = COALESCE(?, parse_status),
                parse_error = COALESCE(?, parse_error),
                processing_state = COALESCE(?, processing_state)
            WHERE file_id = ?
        """, fields)

        conn.commit()
