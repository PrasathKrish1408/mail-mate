import unittest
from unittest.mock import patch, MagicMock
from action_taker import execute_action, authenticate
from database import Database

class TestActionTaker(unittest.TestCase):
    def setUp(self):
        self.mock_service = MagicMock()
        self.mock_db = MagicMock(spec=Database)
        self.email_id = "test_email_id"
        self.mock_email = {
            'id': self.email_id,
            'subject': 'Test Subject',
            'sender': 'test@example.com'
        }
        self.mock_db.get_email.return_value = self.mock_email

    def test_execute_action_mark_as_read_success(self):
        result = execute_action(self.mock_service, self.email_id, 'mark_as_read', self.mock_db)
        self.assertTrue(result)
        self.mock_service.users().messages().modify.assert_called_once()

    def test_execute_action_mark_as_unread_success(self):
        result = execute_action(self.mock_service, self.email_id, 'mark_as_unread', self.mock_db)
        self.assertTrue(result)
        self.mock_service.users().messages().modify.assert_called_once()

    def test_execute_action_move_to_label_success(self):
        label_name = "test_label"
        action = f"move_to_label:{label_name}"
        mock_label = {'id': 'test_label_id', 'name': label_name}
        self.mock_service.users().labels().list.return_value.execute.return_value = {'labels': [mock_label]}
        result = execute_action(self.mock_service, self.email_id, action, self.mock_db)
        self.assertTrue(result)
        self.mock_service.users().messages().modify.assert_called_once()

    def test_execute_action_move_to_label_create_new_label(self):
        label_name = "new_label"
        action = f"move_to_label:{label_name}"
        self.mock_service.users().labels().list.return_value.execute.return_value = {'labels': []}
        mock_new_label = {'id': 'new_label_id', 'name': label_name}
        self.mock_service.users().labels().create.return_value.execute.return_value = mock_new_label
        
        result = execute_action(self.mock_service, self.email_id, action, self.mock_db)
        self.assertTrue(result)
        self.mock_service.users().labels().create.assert_called_once()
        self.mock_service.users().messages().modify.assert_called_once()

    def test_execute_action_unknown_action(self):
        result = execute_action(self.mock_service, self.email_id, 'unknown_action', self.mock_db)
        self.assertFalse(result)
        self.mock_service.users().messages().modify.assert_not_called()

    def test_execute_action_email_not_found(self):
        self.mock_db.get_email.return_value = None
        result = execute_action(self.mock_service, self.email_id, 'mark_as_read', self.mock_db)
        self.assertFalse(result)
        self.mock_service.users().messages().modify.assert_not_called()

    def test_authenticate_returns_credentials(self):
        with patch('action_taker.AuthManager') as mock_auth_manager:
            mock_auth_manager.return_value.authenticate.return_value = 'mock_credentials'
            creds = authenticate()
            self.assertEqual(creds, 'mock_credentials')

if __name__ == '__main__':
    unittest.main()
