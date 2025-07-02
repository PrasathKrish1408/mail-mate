import time
import logging
from googleapiclient.discovery import build
from database import Database
from auth_manager import AuthManager

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def authenticate():
    auth_manager = AuthManager(SCOPES)
    return auth_manager.authenticate()

def execute_action(service, email_id: str, action: str, db) -> bool:
    try:
        email = db.get_email(email_id)
        logger.info(f"Executing action: {action} for email {email_id} with subject {email['subject']} and from {email['sender']}")
        if action == 'mark_as_read':
            service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        elif action == 'mark_as_unread':
            service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()
        elif action.startswith('move_to_label:'):
            label_name = action.split(':')[1]

            labels = service.users().labels().list(userId='me').execute().get('labels', [])
            label_id = None
            
            for label in labels:
                if label['name'] == label_name:
                    label_id = label['id']
                    break
            
            if not label_id:
                try:
                    label = service.users().labels().create(
                        userId='me',
                        body={'name': label_name}
                    ).execute()
                    logger.info(f"Label created: {label['name']}")
                    label_id = label['id']
                except Exception as e:
                    logger.error(f"Error creating label {label_name}: {str(e)}")
                    return False
            
            try:
                service.users().messages().modify(
                    userId='me',
                    id=email_id,
                    body={'addLabelIds': [label_id]}
                ).execute()
            except Exception as e:
                logger.error(f"Error applying label {label_name} to email {email_id}: {str(e)}")
                return False
        else:
            logger.warning(f"Unknown action: {action}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error executing action {action} on email {email_id}: {str(e)}")
        return False

def main():
    db = Database()
    creds = authenticate()
    service = build('gmail', 'v1', credentials=creds)
    
    while True:
        try:
            pending_actions = db.get_pending_actions()
            logger.info(f"Found {len(pending_actions)} pending actions")
            for action in pending_actions:
                success = execute_action(service, action['email_id'], action['action'], db)
                if success:
                    db.update_action_status(action['id'], 'success')
                else:
                    retry_count = action['retry_count'] + 1
                    if retry_count < 3:
                        db.update_action_status(action['id'], 'pending', retry_count)
                    else:
                        db.update_action_status(action['id'], 'failed')
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error in action taker: {str(e)}")
            time.sleep(5)

if __name__ == '__main__':
    main()
