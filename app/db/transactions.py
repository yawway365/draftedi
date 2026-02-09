from app.db.conn import connect


def get_transactions(file_id, transaction_set_id, ack_status):
    where = []
    params = []

    if file_id is not None:
        where.append("f.file_id = ?")
        params.append(file_id)

    if transaction_set_id is not None:
        where.append("t.transaction_set_id = ?")
        params.append(transaction_set_id)

    if ack_status is not None:
        where.append("t.ack_status = ?")
        params.append(ack_status)

    where_sql = ""
    if where:
        where_sql = "WHERE " + " AND ".join(where)

    sql = f"""
    SELECT
        t.transaction_id,
        t.transaction_set_id,
        t.control_number,
        t.implementation_version,
        t.segment_count_reported,
        t.ack_status,
        t.created_at,
        t.group_id,
        g.edi_interchange_id,
        i.file_id,
        f.filename,
        f.parse_status,
        g.functional_id_code,
        g.group_control_number,
        g.x12_release,
        i.isa_sender_id,
        i.isa_receiver_id,
        i.usage_indicator,
        i.version
    FROM edi_transactions t
    JOIN edi_functional_groups g ON g.group_id = t.group_id
    JOIN edi_interchanges i ON i.edi_interchange_id = g.edi_interchange_id
    JOIN edi_files f ON f.file_id = i.file_id
    {where_sql}
    ORDER BY t.transaction_id DESC
    LIMIT ? OFFSET ?;
    """

    with connect() as conn:
        cur = conn.cursor()
        rows = cur.execute(sql, params).fetchall()

    return [dict(r) for r in rows]