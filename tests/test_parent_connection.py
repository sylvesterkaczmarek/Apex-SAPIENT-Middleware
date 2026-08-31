#
# Copyright (c) 2019-2024 Roke Manor Research Ltd
#

from datetime import datetime, timedelta
from unittest.mock import MagicMock

from sapient_apex_server.connection import ParentConnection, SensorInfo, SharedData
from sapient_apex_server.structures import (
    MessageFormat,
    MessageRecord,
    ParsedRecord,
    ReceivedDataRecord,
)


def _message(destination_id=None):
    timestamp = datetime.utcnow()
    return MessageRecord(
        received=ReceivedDataRecord(
            connection_id=1,
            message_id=1,
            timestamp=timestamp,
            data_bytes=b"message",
        ),
        data_decoded_xml="",
        data_binary_proto=b"message",
        decoded_timestamp=timestamp,
        parsed=ParsedRecord(
            message_type="registration_ack",
            node_id="parent-node",
            internal_sensor_id=None,
            destination_node_id=destination_id,
            message_timestamp=timestamp,
            detection_confidence=None,
            parsed_proto=None,
            parsed_xml=None,
        ),
    )


def test_parent_routes_targeted_message_to_child_without_reflection():
    child_writer = MagicMock()
    dmm_writer = MagicMock()
    source_parent_writer = MagicMock()
    other_parent_writer = MagicMock()

    shared_data = SharedData(
        config={},
        middleware_node_id="middleware",
        registered_sensors={},
        next_auto_sensor_id=1,
        dmm_msg_format=MessageFormat.PROTO,
        dmm_writers=[dmm_writer],
        parent_high_level_writers=[],
        parent_all_writers=[],
        parent_message_format=MessageFormat.PROTO,
    )

    source_parent = ParentConnection(
        shared_data,
        source_parent_writer,
        {"forwardAll": True},
        MessageFormat.PROTO,
    )
    ParentConnection(
        shared_data,
        other_parent_writer,
        {"forwardAll": True},
        MessageFormat.PROTO,
    )

    shared_data.registered_sensors["child-node"] = SensorInfo(
        writer=child_writer,
        registration=_message(),
        dmm_msg_offset=timedelta(),
        message_format=MessageFormat.PROTO,
    )

    msg = _message("child-node")
    source_parent.handle_message(msg, MagicMock())

    child_writer.assert_called_once_with(msg, msg.sapient_version)
    dmm_writer.assert_called_once_with(msg, msg.sapient_version)
    source_parent_writer.assert_not_called()
    other_parent_writer.assert_called_once_with(msg, msg.sapient_version)
    assert msg.forwarded_count == 3
