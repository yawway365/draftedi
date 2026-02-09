from app.db.x12 import create_edi_file, create_edi_interchange, create_functional_group, create_transaction, create_segment, create_element, create_component
from app.db.partners import lookup_trading_partner_and_interchange

def ingest_edi_file(edi_file):

    def ingest_segment(segment):
        segment = create_segment(segment)

        for element in segment.get('elements', []):
            element['segment_row_id'] = segment.get('segment_row_id', None)
            element = create_element(element)

            for component in element.get('components', []):
                component['element_row_id'] = element.get('element_row_id', None)
                create_component(component)

        return segment

    edi_file_dict = edi_file.get('edi_file_dict', None)
    interchange_dict = edi_file.get('interchange_dict', None)
    group_dict = edi_file.get('group_dict', None)
    transaction_dict = edi_file.get('transaction_dict', None)
    segments_list = edi_file.get('segments', None)

    # attempt to map to your configured partner/interchange
    partner_id, interchange_id = lookup_trading_partner_and_interchange(
        isa_sender_id=interchange_dict.get('isa_sender_id', None),
        isa_receiver_id=interchange_dict.get('isa_receiver_id', None),
        sender_qual=interchange_dict.get('sender_qual', None),
        receiver_qual=interchange_dict.get('receiver_qual', None),
        gs_sender_id=group_dict.get('gs_sender_id', None),
        gs_receiver_id=group_dict.get('gs_receiver_id', None),
    )

    # Re-assign database generated values, file_id, partner_id, interchange_id
    edi_file['edi_file_dict']['partner_id'] = partner_id
    edi_file['edi_file_dict']['interchange_id'] = interchange_id
    # Create the file record
    edi_file['edi_file_dict'] = create_edi_file(edi_file_dict)

    edi_file['interchange_dict']['file_id'] = edi_file['edi_file_dict']['file_id']
    edi_file['interchange_dict']['partner_id'] = partner_id
    edi_file['interchange_dict']['interchange_id'] = interchange_id
    # Create the interchange record
    edi_file['interchange_dict'] = create_edi_interchange(interchange_dict)

    # Re assign database generate value edi_interchange_id
    edi_file['group_dict']['edi_interchange_id'] = edi_file['interchange_dict']['edi_interchange_id']
    # Create the group record
    edi_file['group_dict'] = create_functional_group(group_dict)

    # Create the transaction record
    edi_file['transaction_dict'] = create_transaction(transaction_dict)

    for segment_dict in segments_list:
        segment_dict = ingest_segment(segment_dict)

    return edi_file
