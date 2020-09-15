import unittest
from unittest.mock import patch, MagicMock, ANY

import json

from gobstuf.audit_log import GOBAuditLogHandler, get_log_handler, get_user_from_request, get_nested_item, on_audit_log_exception

class TestAuditLog(unittest.TestCase):

    def test_log_handler(self):
        log_handler = GOBAuditLogHandler()
        self.assertIsNotNone(log_handler)

    @patch('gobstuf.audit_log.request')
    @patch('gobstuf.audit_log.uuid.uuid4', lambda: 'any uuid')
    @patch('gobstuf.audit_log.AuditLogger')
    @patch('gobstuf.audit_log.on_audit_log_exception')
    def test_emit(self, mock_on_audit_log_exception, mock_audit_logger, mock_request):
        mock_request.headers = {}
        log_handler = GOBAuditLogHandler()

        log_handler.format = MagicMock()
        record = None
        log_handler.emit(record)
        mock_on_audit_log_exception.assert_called_with(ANY, record)

        log_handler.format.side_effect = lambda record: json.dumps(record)
        record = {
            "audit": {
                "http_request": {
                    "url": "any url",
                    "any request data": "any request value",
                },
                "http_response": {
                    "any response data": "any response value",
                },
                "user": {
                    "ip": "any ip",
                    "any user data": "any user value",
                },
                "any audit data": "any audit value"
            }
        }
        log_handler.emit(record)
        mock_audit_logger.get_instance.assert_called_with()
        audit_logger = mock_audit_logger.get_instance.return_value
        audit_logger.log_request.assert_called_with(
            source="any url",
            destination="any ip",
            extra_data={
                **{key: record["audit"][key] for key in ["http_request", "user", "any audit data"]},
                'X-Correlation-ID': None,
                'X-Unique-ID': None,
            },
            request_uuid="any uuid"
        )
        audit_logger.log_response.assert_called_with(
            source="any url",
            destination="any ip",
            extra_data={
                key: record["audit"][key] for key in ["http_response", "user", "any audit data"]
            },
            request_uuid="any uuid"
        )

        # Test with correlation ID and unique ID set
        mock_request.headers = {
            'X-Correlation-ID': 'some correlation id',
            'X-Unique-ID': 'some unique id'
        }
        log_handler.emit(record)
        mock_audit_logger.get_instance.assert_called_with()
        audit_logger = mock_audit_logger.get_instance.return_value
        audit_logger.log_request.assert_called_with(
            source="any url",
            destination="any ip",
            extra_data={
                **{key: record["audit"][key] for key in ["http_request", "user", "any audit data"]},
                'X-Correlation-ID': 'some correlation id',
                'X-Unique-ID': 'some unique id',
            },
            request_uuid="some correlation id"
        )
        audit_logger.log_response.assert_called_with(
            source="any url",
            destination="any ip",
            extra_data={
                key: record["audit"][key] for key in ["http_response", "user", "any audit data"]
            },
            request_uuid="some correlation id"
        )


        mock_on_audit_log_exception.reset_mock()
        audit_logger.log_request.side_effect = Exception("any exception")
        log_handler.emit(record)
        mock_on_audit_log_exception.assert_called_with(audit_logger.log_request.side_effect, record)

    @patch('gobstuf.audit_log.get_client_ip')
    @patch('gobstuf.audit_log.request')
    def test_get_user_from_request(self, mock_request, mock_get_client_ip):
        user = get_user_from_request()
        self.assertEqual(user, {
            'authenticated': False,
            'provider': '',
            'realm': '',
            'email': '',
            'roles': [],
            'ip': mock_get_client_ip.return_value
        })
        mock_get_client_ip.assert_called_with(mock_request)

    def test_get_nested_item(self):
        self.assertEqual(get_nested_item({'a': {'b': {'c': 5}}}, 'a', 'b', 'c'), 5)
        self.assertEqual(get_nested_item({'a': {'b': {'c': 5}}}, 'a', 'b', 'c', 'd'), None)
        self.assertEqual(get_nested_item({'a': {'b': {'c': 5}}}, 'a', 'b', 'd'), None)

    def test_get_log_handler(self):
        log_handler = get_log_handler()
        self.assertIsInstance(log_handler, GOBAuditLogHandler)

    @patch("builtins.print")
    def test_on_audit_log_exception(self, mock_print):
        msg_to_be_logged = 'any message'
        on_audit_log_exception(Exception(), msg_to_be_logged)
        mock_print.assert_called_with(ANY, msg_to_be_logged)
