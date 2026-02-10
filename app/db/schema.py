from app.db.conn import connect

def create_tables() -> None:
    conn = connect()
    cur = conn.cursor()

    #Tables for partner info
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trading_partners (
            partner_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            shortname TEXT,
            is_active INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_DATE,
            contact_name TEXT,
            contact_email TEXT,
            contact_phone TEXT,
            notes TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS interchanges (
            interchange_id INTEGER PRIMARY KEY AUTOINCREMENT,
            interchange_partner_id INTEGER NOT NULL,
            direction TEXT NOT NULL,
            isa_sender_qualifier TEXT NOT NULL,
            isa_sender_id TEXT NOT NULL,
            gs_sender_id TEXT NOT NULL,
            isa_receiver_qualifier TEXT NOT NULL,
            isa_receiver_id TEXT NOT NULL,
            gs_receiver_id TEXT NOT NULL,
            environment TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_DATE,
            
            FOREIGN KEY(interchange_partner_id) REFERENCES trading_partners(partner_id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS interchange_sets (
            interchange_set_id INTEGER PRIMARY KEY AUTOINCREMENT,
            interchange_id INTEGER NOT NULL,
            interchange_transaction_set_id TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 0,
            requires_ack INTEGER NOT NULL DEFAULT 0,
            x12_release TEXT NOT NULL,
            partner_specs TEXT,
            FOREIGN KEY(interchange_id) REFERENCES interchanges(interchange_id)
        );
    """)


    # Tables for EDI Files
    cur.execute("""
    CREATE TABLE IF NOT EXISTS edi_files (
        file_id INTEGER PRIMARY KEY AUTOINCREMENT,
        partner_id INTEGER,
        interchange_id INTEGER,
        processed_at TEXT,
        filename TEXT,
        file_hash TEXT,
        raw_bytes BLOB,
        parse_status TEXT,
        parse_error TEXT,
        processing_state TEXT,
        source TEXT,
        FOREIGN KEY(partner_id) REFERENCES trading_partners(partner_id),
        FOREIGN KEY(interchange_id) REFERENCES interchanges(interchange_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS edi_interchanges (
        edi_interchange_id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        partner_id INTEGER,
        interchange_id INTEGER,
        isa_control_number TEXT,
        isa_sender_qualifier TEXT,
        isa_sender_id TEXT,
        isa_receiver_qualifier TEXT,
        isa_receiver_id TEXT,
        isa_date TEXT,
        isa_time TEXT,
        usage_indicator TEXT,
        version TEXT,
        element_sep TEXT NOT NULL DEFAULT '*',
        component_sep TEXT,
        segment_term TEXT NOT NULL DEFAULT '~',
        repetition_sep TEXT,
        raw_isa TEXT,
        FOREIGN KEY(file_id) REFERENCES edi_files(file_id),
        FOREIGN KEY(partner_id) REFERENCES trading_partners(partner_id),
        FOREIGN KEY(interchange_id) REFERENCES interchanges(interchange_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS edi_functional_groups (
        group_id INTEGER PRIMARY KEY AUTOINCREMENT,
        edi_interchange_id INTEGER NOT NULL,
        functional_id_code TEXT,
        gs_sender_id TEXT,
        gs_receiver_id TEXT,
        group_control_number TEXT,
        x12_release TEXT,
        raw_gs_segment TEXT,
        FOREIGN KEY(edi_interchange_id) REFERENCES edi_interchanges(edi_interchange_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS edi_transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        transaction_set_id TEXT,
        control_number TEXT,
        implementation_version TEXT,
        segment_count_reported INTEGER,
        raw_st_segment TEXT,
        raw_se_segment TEXT,
        ack_status TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(group_id) REFERENCES edi_functional_groups(group_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS edi_segments (
        segment_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER NOT NULL,
        position INTEGER NOT NULL,
        segment_id TEXT NOT NULL,
        loop_path TEXT,
        raw_segment TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(transaction_id) REFERENCES edi_transactions(transaction_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS edi_elements (
        element_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
        segment_row_id INTEGER NOT NULL,
        element_pos INTEGER NOT NULL,
        is_composite INTEGER NOT NULL DEFAULT 0,
        value_text TEXT,
        present INTEGER NOT NULL DEFAULT 1,
        repetition_index INTEGER NOT NULL DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(segment_row_id) REFERENCES edi_segments(segment_row_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS edi_components (
        component_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
        element_row_id INTEGER NOT NULL,
        component_pos INTEGER NOT NULL,
        value_text TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(element_row_id) REFERENCES edi_elements(element_row_id)
    );
    """)

    # Mapping for a transaction set to a template
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transaction_set_mappings (
            mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
            interchange_set_id INTEGER NOT NULL,
            mapping_name TEXT,
            mapping_version TEXT DEFAULT '1.0',
            
            template_json TEXT NOT NULL, -- store template as json
            
            -- Optional: store sample input/output for testing
            sample_input_json TEXT,
            sample_output_edi TEXT,
            
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY(interchange_set_id) REFERENCES interchange_sets(interchange_set_id)
        );
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_edi_files_hash ON edi_files(file_hash);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_edi_segments_tx_pos ON edi_segments(transaction_id, position);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_edi_elements_seg_pos ON edi_elements(segment_row_id, element_pos);")


    conn.commit()
    conn.close()
