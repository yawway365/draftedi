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


def get_partner(trading_partner_id):
    with connect() as conn:
        cursor = conn.cursor()

        sql = """
            SELECT
                tp.partner_id,
                tp.name,
                tp.shortname,
                tp.is_active,
                tp.created_at,
                tp.contact_name,
                tp.contact_email,
                tp.contact_phone,
                tp.notes
            FROM trading_partners as tp
            WHERE tp.partner_id = ?
        """, (str(trading_partner_id))

        cursor.execute(sql)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]

def get_all_partners():
    with connect() as conn:
        cursor = conn.cursor()

        sql = """
            SELECT 
                tp.partner_id,
                tp.name,
                tp.shortname,
                tp.is_active,
                tp.created_at,
                tp.contact_name,
                tp.contact_email,
                tp.contact_phone,
                tp.notes
            FROM trading_partners tp
        """

        cursor.execute(sql)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]

def get_partner_interchanges(trading_partner_id):
    with connect() as conn:
        cursor = conn.cursor()

        sql = """
            SELECT 
                tp.partner_id,
                    
                i.interchange_id,
                i.direction,
                i.environment,
                i.isa_sender_qualifier,
                i.isa_sender_id,
                i.gs_sender_id,
                i.isa_receiver_qualifier,
                i.isa_receiver_id,
                i.gs_receiver_id,
                i.is_active as interchange_is_active,
                i.created_at
                    
            FROM trading_partners tp
            JOIN interchanges i
                ON i.interchange_partner_id = tp.partner_id
            WHERE tp.partner_id = ?
            ORDER BY i.direction
        """, (str(trading_partner_id))

        cursor.execute(sql)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]

def get_partner_interchange_sets(trading_partner_id):
    with connect() as conn:
        cursor = conn.cursor()

        sql = """
            SELECT 
                tp.partner_id,
                    
                i.interchange_id,
                i.direction,
                i.environment,
                i.isa_sender_qualifier,
                i.isa_sender_id,
                i.gs_sender_id,
                i.isa_receiver_qualifier,
                i.isa_receiver_id,
                i.gs_receiver_id,
                i.is_active,
                i.created_at,
                
                iset.interchange_set_id,
                iset.interchange_transaction_set_id,
                iset.requires_ack,
                iset.is_active,
                iset.x12_release,
                iset.partner_specs
                    
            FROM trading_partners tp
            JOIN interchanges i
                ON i.interchange_partner_id = tp.partner_id
            LEFT JOIN interchange_sets iset
                ON iset.interchange_id = i.interchange_id
            WHERE tp.partner_id = ?
            ORDER BY i.direction, iset.interchange_transaction_set_id
        """, (str(trading_partner_id))

        cursor.execute(sql)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def create_partner(trading_partner_dict):
    fields = (
        trading_partner_dict.get('name'),
        trading_partner_dict.get('shortname'),
        trading_partner_dict.get('contact_name'),
        trading_partner_dict.get('contact_email'),
        trading_partner_dict.get('contact_phone'),
    )

    with connect() as conn:
        cursor = conn.cursor()

        cursor.execute(("""
            INSERT INTO trading_partners
                (name, shortname, contact_name, contact_email, contact_phone)
            VALUES
                (?, ?, ?, ?, ?)
        """), fields)

        partner_id = cursor.lastrowid
        trading_partner_dict["partner_id"] = partner_id

        conn.commit()

    return trading_partner_dict

def create_partner_interchange(interchange_dict):
    fields = (
        interchange_dict.get('interchange_partner_id'),
        interchange_dict.get('direction'),
        interchange_dict.get('isa_sender_qualifier'),
        interchange_dict.get('isa_sender_id'),
        interchange_dict.get('gs_sender_id'),
        interchange_dict.get('isa_receiver_qualifier'),
        interchange_dict.get('isa_receiver_id'),
        interchange_dict.get('gs_receiver_id'),
        interchange_dict.get('environment'),
        interchange_dict.get('is_active'),
    )

    with connect() as conn:
        cursor = conn.cursor()

        cursor.execute(("""
            INSERT INTO interchanges
                (interchange_partner_id, direction, isa_sender_qualifier, isa_sender_id, gs_sender_id, 
                isa_receiver_qualifier, isa_receiver_id, gs_receiver_id, environment, is_active)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """), fields)

        interchange_id = cursor.lastrowid
        interchange_dict["interchange_id"] = interchange_id

        conn.commit()

    return interchange_dict

def create_interchange_set(interchange_set_dict):
    fields = (
        interchange_set_dict.get('interchange_id'),
        interchange_set_dict.get('interchange_transaction_set_id'),
        interchange_set_dict.get('is_active'),
        interchange_set_dict.get('requires_ack'),
        interchange_set_dict.get('x12_release'),
        interchange_set_dict.get('partner_specs'),
    )

    with connect() as conn:
        cursor = conn.cursor()

        cursor.execute(("""
            INSERT INTO interchange_sets
                (interchange_id, interchange_transaction_set_id, is_active, requires_ack, x12_release, partner_specs)
            VALUES
                (?, ?, ?, ?, ?, ?)
        """), fields)

        interchange_set_id = cursor.lastrowid
        interchange_set_dict['interchange_set_id'] = interchange_set_id

        conn.commit()

        return interchange_set_dict

def update_interchange_set(interchange_set_dict):
    interchange_set_id = interchange_set_dict.get("interchange_set_id")

    fields = (
        interchange_set_dict.get('interchange_id'),
        interchange_set_dict.get('interchange_transaction_set_id'),
        interchange_set_dict.get('is_active'),
        interchange_set_dict.get('requires_ack'),
        interchange_set_dict.get('x12_release'),
        interchange_set_dict.get('partner_specs'),
        interchange_set_id
    )

    with connect() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE interchange_sets
            SET
                interchange_id = ?,
                interchange_transaction_set_id = ?,
                is_active = ?,
                requires_ack = ?,
                x12_release = ?,
                partner_specs = ?
            WHERE interchange_set_id = ?
        """, fields)

        conn.commit()

    return interchange_set_dict
