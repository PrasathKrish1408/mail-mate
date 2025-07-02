import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import re
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_email_dict_key(field: str) -> str:
    if field == 'from':
        return 'sender'
    return field


class RuleEvaluator:
    def __init__(self, rules_path: str = 'rules.json'):
        self.rules_path = rules_path
        self.load_rules()

    def load_rules(self):
        with open(self.rules_path, 'r') as f:
            self.rulesets = json.load(f)['rulesets']

    def evaluate_rule(self, email: Dict, rule: Dict) -> bool:
        field = rule['field']
        predicate = rule['predicate']
        value = rule['value']
        email_value = email.get(get_email_dict_key(field.lower()), '')
        
        # String predicates
        if predicate == 'contains':
            result = value.lower() in email_value.lower()
            logger.info(f'Evaluating {field.lower()}: {value} -> {email_value} for predicate {predicate} and result {result}')
            return result
        elif predicate == 'does_not_contain':
            result = value.lower() not in email_value.lower()
            logger.info(f'Evaluating {field.lower()}: {value} -> {email_value} for predicate {predicate} and result {result}')
            return result
        elif predicate == 'equals':
            result = email_value.lower() == value.lower()
            logger.info(f'Evaluating {field.lower()}: {value} -> {email_value} for predicate {predicate} and result {result}')
            return result
        elif predicate == 'does_not_equal':
            result = email_value.lower() != value.lower()
            logger.info(f'Evaluating {field.lower()}: {value} -> {email_value} for predicate {predicate} and result {result}')
            return result
        
        # Date predicates
        elif predicate in ['greater_than_days', 'less_than_days', 'greater_than_months', 'less_than_months']:
            try:
                # Convert value to integer (days or months)
                value_num = int(value)
                
                # Get received time and convert to datetime if needed
                received_time = email['received']
                if isinstance(received_time, str):
                    received_time = datetime.fromisoformat(received_time)
                
                # Calculate cutoff time based on predicate
                if 'days' in predicate:
                    delta = timedelta(days=value_num)
                else:  # months
                    delta = timedelta(days=value_num * 30)  # Approximate months as 30 days
                
                cutoff = datetime.now() - delta
                
                # Compare based on predicate type
                if predicate == 'greater_than_days':
                    result = received_time < cutoff
                elif predicate == 'less_than_days':
                    result = received_time > cutoff
                elif predicate == 'greater_than_months':
                    result = received_time < cutoff
                elif predicate == 'less_than_months':
                    result = received_time > cutoff
                
                logger.info(f'Evaluating {field.lower()}: {value} days/months -> {received_time} for predicate {predicate} and result {result}')
                return result
                
            except (ValueError, TypeError) as e:
                logger.error(f"Error in date comparison: {str(e)}")
                return False
        
        else:
            logger.warning(f"Unknown predicate: {predicate}")
            return False

    def evaluate_ruleset(self, email: Dict, ruleset: Dict) -> bool:
        rules = ruleset['rules']
        predicate = ruleset['global_predicate'].lower()
        
        if predicate == 'any':
            return any(self.evaluate_rule(email, rule) for rule in rules)
        elif predicate == 'all':
            return all(self.evaluate_rule(email, rule) for rule in rules)
        else:
            logger.warning(f"Unknown global predicate: {predicate}")
            return False

    def get_matching_actions(self, email: Dict) -> List[Dict]:
        matching_actions = []
        for ruleset in self.rulesets:
            if self.evaluate_ruleset(email, ruleset):
                # Create a dictionary with rule name and actions
                matching_actions.append({
                    'rule_name': ruleset['name'],
                    'actions': ruleset.get('actions', [])
                })
        return matching_actions

def main():
    db = Database()
    evaluator = RuleEvaluator()
    
    while True:
        try:
            new_emails = db.get_new_emails()
            logger.info(f"Processing {len(new_emails)} new emails")
            
            for email in new_emails:
                matching_actions = evaluator.get_matching_actions(email)
                for action_set in matching_actions:
                    rule_name = action_set['rule_name']
                    for action in action_set['actions']:
                        db.add_action(email['id'], action, rule_name)
                db.update_email_processed(email)
            time.sleep(20)
        except Exception as e:
            logger.error(f"Error in rule engine: {str(e)}")
            time.sleep(5)

if __name__ == '__main__':
    main()
