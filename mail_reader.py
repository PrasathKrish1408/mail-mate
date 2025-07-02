import os
import time
import logging
import datetime
from googleapiclient.discovery import build
from database import Database
from auth_manager import AuthManager

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def authenticate():
    """Authenticate with Google API and return credentials."""
    auth_manager = AuthManager(SCOPES)
    return auth_manager.authenticate()

def fetch_emails(service, db: Database):
    try:
        # Get last fetched time and subtract 1 day
        last_fetched_time = db.get_last_fetched_time()
        if isinstance(last_fetched_time, str):
            last_fetched_time = datetime.datetime.fromisoformat(last_fetched_time)
        last_fetched_time = last_fetched_time - datetime.timedelta(days=1)
        query = f'after:{last_fetched_time.strftime("%Y/%m/%d")}'
        logger.info(f'Fetching emails from {query}')
        
        page_token = None
        total_fetched = 0
        run = 1
        while True:
            logger.info(f"Fetching page: {run} of emails")
            run += 1
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=300,
                pageToken=page_token
            ).execute()
            
            messages = results.get('messages', [])
            if not messages:
                break
            
            for message in messages:
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject']
                ).execute()
                
                headers = {}
                for header in msg['payload']['headers']:
                    headers[header['name'].lower()] = header['value']
                
                email_data = {
                    'id': message['id'],
                    'sender': headers.get('from', ''),
                    'subject': headers.get('subject', ''),
                    'snippet': msg['snippet'],
                    'received': datetime.datetime.fromtimestamp(
                        int(msg['internalDate']) / 1000
                    ),
                    'is_read': 'UNREAD' not in msg['labelIds']
                }
                
                db.add_email(email_data)
            
            total_fetched += len(messages)
            page_token = results.get('nextPageToken')
            
            if not page_token:
                break
        
        if total_fetched > 0:
            db.update_last_fetched_time(datetime.datetime.now())
        logger.info(f"Fetched {total_fetched} new emails")
        
    except Exception as e:
        logger.error(f"Error fetching emails: {str(e)}")

def main():
    db = Database()
    creds = authenticate()
    service = build('gmail', 'v1', credentials=creds)
    
    while True:
        fetch_emails(service, db)
        time.sleep(20)  # Poll every 20 seconds

if __name__ == '__main__':
    main()
