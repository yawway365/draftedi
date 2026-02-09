from app.db.conn import connect

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