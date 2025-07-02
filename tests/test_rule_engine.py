import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from rule_engine import RuleEvaluator, get_email_dict_key

class TestRuleEngine(unittest.TestCase):
    def setUp(self):
        self.evaluator = RuleEvaluator()
        self.mock_email = {
            'id': 'test_email_id',
            'subject': 'Test Subject',
            'sender': 'test@example.com',
            'received': datetime.now().isoformat()
        }

    def test_get_email_dict_key(self):
        self.assertEqual(get_email_dict_key('from'), 'sender')
        self.assertEqual(get_email_dict_key('subject'), 'subject')
        self.assertEqual(get_email_dict_key('body'), 'body')

    def test_evaluate_rule_contains(self):
        rule = {'field': 'subject', 'predicate': 'contains', 'value': 'Test'}
        result = self.evaluator.evaluate_rule(self.mock_email, rule)
        self.assertTrue(result)

    def test_evaluate_rule_does_not_contain(self):
        rule = {'field': 'from', 'predicate': 'does_not_contain', 'value': 'spam'}
        result = self.evaluator.evaluate_rule(self.mock_email, rule)
        self.assertTrue(result)

    def test_evaluate_rule_equals(self):
        rule = {'field': 'from', 'predicate': 'equals', 'value': 'test@example.com'}
        result = self.evaluator.evaluate_rule(self.mock_email, rule)
        self.assertTrue(result)

    def test_evaluate_rule_does_not_equal(self):
        rule = {'field': 'from', 'predicate': 'does_not_equal', 'value': 'spam@example.com'}
        result = self.evaluator.evaluate_rule(self.mock_email, rule)
        self.assertTrue(result)

    def test_evaluate_rule_greater_than_days(self):
        two_days_ago = datetime.now() - timedelta(days=2)
        self.mock_email['received'] = two_days_ago.isoformat()
        rule = {'field': 'received', 'predicate': 'greater_than_days', 'value': '1'}
        result = self.evaluator.evaluate_rule(self.mock_email, rule)
        self.assertTrue(result)

    def test_evaluate_rule_less_than_days(self):
        two_days_ago = datetime.now() - timedelta(days=2)
        self.mock_email['received'] = two_days_ago.isoformat()
        rule = {'field': 'received', 'predicate': 'less_than_days', 'value': '3'}
        result = self.evaluator.evaluate_rule(self.mock_email, rule)
        self.assertTrue(result)

    def test_evaluate_ruleset_any(self):
        ruleset = {
            'global_predicate': 'any',
            'rules': [
                {'field': 'subject', 'predicate': 'contains', 'value': 'Test'},
                {'field': 'sender', 'predicate': 'equals', 'value': 'wrong@example.com'}
            ]
        }
        result = self.evaluator.evaluate_ruleset(self.mock_email, ruleset)
        self.assertTrue(result)

    def test_evaluate_ruleset_all(self):
        ruleset = {
            'global_predicate': 'all',
            'rules': [
                {'field': 'subject', 'predicate': 'contains', 'value': 'Test'},
                {'field': 'sender', 'predicate': 'equals', 'value': 'test@example.com'}
            ]
        }
        result = self.evaluator.evaluate_ruleset(self.mock_email, ruleset)
        self.assertTrue(result)

    def test_get_matching_actions(self):
        ruleset = {
            'name': 'Test Ruleset',
            'global_predicate': 'all',
            'rules': [
                {'field': 'subject', 'predicate': 'contains', 'value': 'Test'}
            ],
            'actions': ['mark_as_read', 'move_to_label:Important']
        }
        self.evaluator.rulesets = [ruleset]
        
        actions = self.evaluator.get_matching_actions(self.mock_email)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['rule_name'], 'Test Ruleset')
        self.assertEqual(actions[0]['actions'], ['mark_as_read', 'move_to_label:Important'])

    def test_get_matching_actions_no_match(self):
        ruleset = {
            'name': 'Test Ruleset',
            'global_predicate': 'all',
            'rules': [
                {'field': 'subject', 'predicate': 'contains', 'value': 'Spam'}
            ],
            'actions': ['mark_as_read']
        }
        self.evaluator.rulesets = [ruleset]
        
        actions = self.evaluator.get_matching_actions(self.mock_email)
        self.assertEqual(len(actions), 0)

if __name__ == '__main__':
    unittest.main()
