import unittest
from unittest.mock import patch, MagicMock

import json

from gobstuf.audit_log import GOBAuditLogHandler, AuditLogException, get_log_handler, get_user_from_request, get_nested_item

class TestAuditLog(unittest.TestCase):

    def test_log_handler(self):
        log_handler = GOBAuditLogHandler()
        self.assertIsNotNone(log_handler)

    @patch('gobstuf.audit_log.uuid.uuid4', lambda: 'any uuid')
    @patch('gobstuf.audit_log.AuditLogger')
    def test_emit(self, mock_audit_logger):
        log_handler = GOBAuditLogHandler()

        log_handler.format = MagicMock()
        record = None
        with self.assertRaises(AuditLogException):
            log_handler.emit(record)

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
              key: record["audit"][key] for key in ["http_request", "user", "any audit data"]
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
