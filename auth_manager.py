import os
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)


class AuthManager:
    def __init__(self, scopes=None):
        self.scopes = scopes or ['https://www.googleapis.com/auth/gmail.readonly']

    def authenticate(self):

        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.scopes)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.scopes)
                creds = flow.run_local_server(port=56741)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        logger.info(f'Access Token: {creds.token}')
        return creds
