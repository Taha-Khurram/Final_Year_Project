import os
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials


class GoogleSheetsService:
    _instance = None
    _worksheet = None

    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    HEADERS = ['Timestamp', 'User', 'Action Type', 'Action', 'Blog Title', 'Details']

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        self._client = None

    def _get_worksheet(self):
        if self._worksheet is not None:
            return self._worksheet

        if not self._spreadsheet_id:
            return None

        try:
            creds = Credentials.from_service_account_file(
                'serviceAccountKey.json', scopes=self.SCOPES
            )
            self._client = gspread.authorize(creds)
            spreadsheet = self._client.open_by_key(self._spreadsheet_id)

            try:
                self._worksheet = spreadsheet.worksheet('Activity Log')
            except gspread.WorksheetNotFound:
                self._worksheet = spreadsheet.sheet1
                self._worksheet.update_title('Activity Log')

            if self._worksheet.row_values(1) != self.HEADERS:
                self._worksheet.update('A1:F1', [self.HEADERS])
                self._worksheet.format('A1:F1', {'textFormat': {'bold': True}})

            return self._worksheet
        except Exception as e:
            print(f"Google Sheets init error: {e}")
            return None

    USER_HEADERS = ['UID', 'Name', 'Email', 'Role', 'Created By', 'Created At', 'Last Login']

    def _get_spreadsheet(self):
        if self._client is None:
            if not self._spreadsheet_id:
                return None
            creds = Credentials.from_service_account_file(
                'serviceAccountKey.json', scopes=self.SCOPES
            )
            self._client = gspread.authorize(creds)
        return self._client.open_by_key(self._spreadsheet_id)

    def _get_users_worksheet(self):
        try:
            spreadsheet = self._get_spreadsheet()
            if not spreadsheet:
                return None
            try:
                return spreadsheet.worksheet('Users')
            except gspread.WorksheetNotFound:
                ws = spreadsheet.add_worksheet(title='Users', rows=100, cols=10)
                ws.update(range_name='A1:G1', values=[self.USER_HEADERS])
                ws.format('A1:G1', {'textFormat': {'bold': True}})
                return ws
        except Exception as e:
            print(f"Google Sheets users worksheet error: {e}")
            return None

    def sync_user(self, uid, name, email, role, created_by="", created_at=None, last_login=None):
        try:
            ws = self._get_users_worksheet()
            if not ws:
                return False

            created_str = created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if created_at else ''
            login_str = last_login.strftime('%Y-%m-%d %H:%M:%S UTC') if last_login else ''
            row_data = [uid, name, email, role, created_by, created_str, login_str]

            cell = ws.find(uid, in_column=1)
            if cell:
                ws.update(range_name=f'A{cell.row}:G{cell.row}', values=[row_data])
            else:
                ws.append_row(row_data, value_input_option='USER_ENTERED')
            return True
        except Exception as e:
            print(f"Google Sheets sync user error: {e}")
            return False

    BLOG_HEADERS = ['Blog ID', 'Title', 'Author', 'Status', 'Category', 'Author ID', 'Created At', 'Updated At']

    def _get_blogs_worksheet(self):
        try:
            spreadsheet = self._get_spreadsheet()
            if not spreadsheet:
                return None
            for ws in spreadsheet.worksheets():
                if ws.id == 767306744:
                    return ws
            ws = spreadsheet.add_worksheet(title='Blogs', rows=100, cols=10)
            ws.update(range_name='A1:H1', values=[self.BLOG_HEADERS])
            ws.format('A1:H1', {'textFormat': {'bold': True}})
            return ws
        except Exception as e:
            print(f"Google Sheets blogs worksheet error: {e}")
            return None

    def sync_blog(self, blog_id, title, status, category="", author_id="", created_at=None, updated_at=None, author_name=""):
        try:
            ws = self._get_blogs_worksheet()
            if not ws:
                return False

            created_str = created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if created_at else ''
            updated_str = updated_at.strftime('%Y-%m-%d %H:%M:%S UTC') if updated_at else ''
            row_data = [blog_id, title, author_name, status, category, author_id, created_str, updated_str]

            cell = ws.find(blog_id, in_column=1)
            if cell:
                ws.update(range_name=f'A{cell.row}:H{cell.row}', values=[row_data])
            else:
                ws.append_row(row_data, value_input_option='USER_ENTERED')
            return True
        except Exception as e:
            print(f"Google Sheets sync blog error: {e}")
            return False

    def log_activity(self, user_name, action_type, action_text, blog_title="", details=""):
        try:
            ws = self._get_worksheet()
            if not ws:
                return False

            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            row = [timestamp, user_name, action_type, action_text, blog_title, details]
            ws.append_row(row, value_input_option='USER_ENTERED')
            return True
        except Exception as e:
            print(f"Google Sheets log error: {e}")
            self._worksheet = None
            return False
