import sqlite3
import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = 'rulemate.db'):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create emails table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emails (
                    id TEXT PRIMARY KEY,
                    sender TEXT,
                    subject TEXT,
                    snippet TEXT,
                    received DATETIME,
                    is_read BOOLEAN,
                    is_processed BOOLEAN default false,
                    fetched_at TIMESTAMP
                )
            ''')
            
            # Create checkpoint table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS checkpoint (
                    id INTEGER PRIMARY KEY,
                    last_fetched_timestamp TIMESTAMP
                )
            ''')
            
            # Create action_queue table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS action_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id TEXT,
                    action TEXT,
                    status TEXT,
                    retry_count INTEGER DEFAULT 0,
                    from_rule_name TEXT(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (email_id) REFERENCES emails (id)
                )
            ''')
            
            # Initialize checkpoint if it doesn't exist
            cursor.execute('SELECT COUNT(*) FROM checkpoint')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO checkpoint (last_fetched_timestamp) VALUES (?)', 
                             (datetime.datetime.now(),))
            
            conn.commit()

    def get_last_fetched_time(self) -> datetime.datetime:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT last_fetched_timestamp FROM checkpoint')
            return cursor.fetchone()[0]

    def update_last_fetched_time(self, timestamp: datetime.datetime):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE checkpoint SET last_fetched_timestamp = ?', (timestamp,))
            conn.commit()

    def add_email(self, email_data: Dict[str, str]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO emails (id, sender, subject, snippet, received, is_read, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                email_data['id'],
                email_data['sender'],
                email_data['subject'],
                email_data['snippet'],
                email_data['received'],
                email_data['is_read'],
                datetime.datetime.now()
            ))
            conn.commit()

    def get_new_emails(self) -> List[Dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM emails 
                WHERE is_processed=false
            ''')
            return [dict(zip([col[0] for col in cursor.description], row)) 
                    for row in cursor.fetchall()]

    def add_action(self, email_id: str, action: str, rule_name : str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO action_queue (email_id, action, status, from_rule_name)
                VALUES (?, ?, ?,?)
            ''', (email_id, action, 'pending', rule_name))
            conn.commit()

    def get_pending_actions(self) -> List[Dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM action_queue 
                WHERE status = 'pending'
                ORDER BY created_at ASC
            ''')
            return [dict(zip([col[0] for col in cursor.description], row)) 
                    for row in cursor.fetchall()]

    def update_action_status(self, action_id: int, status: str, retry_count: int = 0):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE action_queue 
                SET status = ?, retry_count = ?
                WHERE id = ?
            ''', (status, retry_count, action_id))
            conn.commit()

    def get_email(self, email_id: str) -> Optional[Dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM emails 
                WHERE id = ?
            ''', (email_id,))
            row = cursor.fetchone()
            if row:
                return dict(zip([col[0] for col in cursor.description], row))
            return None

    def update_email_processed(self, email: Dict):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                   UPDATE emails
                   SET is_processed = true
                   WHERE id = ?
            ''', (email['id'],))
            conn.commit()
