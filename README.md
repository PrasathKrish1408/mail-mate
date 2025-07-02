# Gmail Rule-Based Automation System

A Python-based system that integrates with Gmail API to perform rule-based actions on emails.

## Features

- OAuth2 authentication with Gmail API
- Rule-based email processing
- SQLite database for email storage and action tracking
- Automatic email fetching and rule evaluation
- Retry mechanism for failed actions

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Google Cloud Project:
   - Go to Google Cloud Console
   - Create a new project
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download credentials.json and place it in the project root

3. Create rules.json with your desired rules

## Running the System

The system consists of three main components:

1. Mail Reader (mail_reader.py)
2. Rule Processor (rule_engine.py)
3. Action Taker (action_taker.py)

You can run each component separately:
```bash
python mail_reader.py
python rule_engine.py
python action_taker.py
```

## Database Schema

The system uses SQLite with three tables:
- emails: Stores email metadata
- checkpoint: Tracks the timestamp when emails are last fetched.
- action_queue: Manages pending actions

## Rules Format

Example rules.json:
```json
{
    "rulesets": [
        {
            "name": "Invoice Processing",
            "global_predicate": "Any",
            "rules": [
                {
                    "field": "subject",
                    "predicate": "contains",
                    "value": "invoice"
                },
                {
                    "field": "from",
                    "predicate": "equals",
                    "value": "billing@example.com"
                }
            ],
            "actions": ["move_to_label:Invoices"]
        }
    ]
}
```
