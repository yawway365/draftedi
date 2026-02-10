from app.db.conn import connect_edi

AREA_MAP = {
    1: 'header',
    2: 'detail',
    3: 'summary'
}

def get_all_transaction_sets(version):

    with connect_edi(version) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                transaction_set_id,
                transaction_set_name,
                transaction_set_functional_group_id,
                transaction_set_purpose
            FROM transaction_sets
        """, (
        ))

        rows = [dict(row) for row in cursor.fetchall()]

        return rows

def get_transaction_set(version, transaction_set_id):
    with connect_edi(version) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                transaction_set_id,
                transaction_set_name,
                transaction_set_functional_group_id,
                transaction_set_purpose
            FROM transaction_sets
            WHERE transaction_set_id = ?
        """, (
            transaction_set_id,
        ))

    row = dict(cursor.fetchone())

    transaction_segments = get_transaction_set_segments(cursor, version, transaction_set_id)
    row['segments'] = transaction_segments

    return row if row else None

# conn needed before and passed through to avoid multiple connections and to support transactionality if needed in the future. You must use the same connection to ensure you are querying the same database state, especially if using WAL mode where readers can see committed changes from other connections but not uncommitted changes.    
def get_transaction_set_segments(cursor, version, transaction_set_id):
    cursor.execute("""
        SELECT 
            transaction_set_segment_id,
            transaction_set_id,
            segment_id,
            segment_loop_id,
            segment_sequence,
            segment_area,
            segment_requirement,
            segment_maximum_use,
            segment_loop_level,
            segment_loop_repeat
        FROM transaction_set_segments
        WHERE transaction_set_id = ? 
        ORDER BY transaction_set_segment_id
    """, (
        transaction_set_id,
    ))

    rows = [dict(row) for row in cursor.fetchall()]

    for row in rows:
        row['segment_area_name'] = AREA_MAP.get(row.get('segment_area'))

    final_rows = []
    loop_stack = []
    for row in rows:
        transaction_set_segment_id = row.get("transaction_set_segment_id")
        segment_id = row.get("segment_id")
        loop_id = row.get("segment_loop_id")
        is_loop_marker = segment_id is None and loop_id is not None

        if is_loop_marker:
            # stack is empty (no loop) or top loop_id mismatch (new loop inside loop), start a new
            if not loop_stack or loop_stack[-1]['loop_id'] != loop_id:
                loop_stack.append({'loop_id': loop_id, 'segments': []})
            else:
                finished = loop_stack.pop()
                finished_segments = finished['segments']

                if loop_stack:
                    # inside parent loop, add loop to parent
                    loop_stack[-1]['segments'].append(finished_segments)
                else:
                    final_rows.append(finished_segments)
            
            #skip adding marker rows
            continue

        row['segment_notes'] = get_transaction_set_segment_notes(cursor, transaction_set_segment_id)
        row['segment_relational_conditions'] = get_transaction_set_relational_conditions(version, transaction_set_segment_id)
        row['segment_elements'] = get_segment_elements(version, segment_id)
        
        if loop_stack:
            #inside loop: attach to top loop
            loop_stack[-1]['segments'].append(row)
        else:
            # top level segment
            final_rows.append(row)
        
    # If loop_stack not empty, you have unclosed loops in your data
    if loop_stack:
        # You can either raise or just flush them somehow; raising is safer:
        raise ValueError(f"Unclosed loops found: {[f['loop_id'] for f in loop_stack]}")


    return final_rows if final_rows else None

def get_transaction_set_segment_notes(cursor, transaction_set_segment_id):

    cursor.execute("""
        SELECT 
            transaction_set_segment_id,
            transaction_set_segment_note_type,
            transaction_set_segment_note_paragraph_number,
            transaction_set_segment_note_content
        FROM transaction_set_segment_notes
        WHERE transaction_set_segment_id = ? 
        ORDER BY transaction_set_segment_id
    """, (
        transaction_set_segment_id,
    ))

    rows = [dict(row) for row in cursor.fetchall()]

    return rows

def get_transaction_set_relational_conditions(cursor, transaction_set_segment_id):

    cursor.execute("""
        SELECT 
            transaction_set_segment_id,
            transaction_set_segment_rc_elements,
            transaction_set_segment_rc_type
        FROM transaction_set_segment_relational_conditions
        WHERE transaction_set_segment_id = ? 
        ORDER BY transaction_set_segment_id
    """, (
        transaction_set_segment_id,
    ))

    rows = [dict(row) for row in cursor.fetchall()]
    
    if rows:
        for row in rows:
            row['transaction_set_segment_rc_elements'] = [element.strip() for element in row['transaction_set_segment_rc_elements'].split(',')]

    return rows


def get_segment_elements(cursor, segment_id):
    cursor.execute("""
        SELECT 
            se.segment_element_id,
            se.segment_id,
            se.element_id,
            se.segment_element_requirement,
            se.segment_element_sequence,
            se.segment_element_repetition_count,
            e.element_name,
            e.element_type,
            e.element_definition,
            e.element_max_length,
            e.element_min_length,
            e.element_code_count
        FROM segment_elements as se
        LEFT JOIN elements as e ON se.element_id = e.element_id
        WHERE segment_id = ? 
        ORDER BY segment_element_id
    """, (
        segment_id,
    ))

    rows = [dict(row) for row in cursor.fetchall()]

    if rows:
        for row in rows:
            segment_element_id = row.get('segment_element_id')
            row['segment_element_notes'] = get_segment_element_notes(cursor, segment_element_id)
    
    return rows

def get_segment_element_notes(cursor, segment_element_id):
    cursor.execute("""
        SELECT 
            segment_element_id,
            segment_element_note_content,
            segment_element_note_paragraph_number,
            segment_element_note_type
        FROM segment_element_notes
        WHERE segment_element_id = ? 
        ORDER BY segment_element_id
    """, (
        segment_element_id,
    ))

    rows = [dict(row) for row in cursor.fetchall()]  

    return rows
