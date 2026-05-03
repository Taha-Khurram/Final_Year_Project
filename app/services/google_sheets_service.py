import os
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials


class GoogleSheetsService:
    _instance = None

    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    HEADERS = ['Timestamp', 'User', 'Action Type', 'Action', 'Blog Title', 'Details']
    USER_HEADERS = ['UID', 'Name', 'Email', 'Role', 'Created By', 'Created At', 'Last Login']
    BLOG_HEADERS = ['Blog ID', 'Title', 'Author', 'Status', 'Category', 'Author ID', 'Created At', 'Updated At']

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._default_spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        self._client = None
        self._worksheet_cache = {}

    def _get_client(self):
        if self._client is None:
            creds = Credentials.from_service_account_file(
                'serviceAccountKey.json', scopes=self.SCOPES
            )
            self._client = gspread.authorize(creds)
        return self._client

    def _resolve_spreadsheet_id(self, spreadsheet_id=None):
        return spreadsheet_id or self._default_spreadsheet_id

    def _get_spreadsheet(self, spreadsheet_id=None):
        sid = self._resolve_spreadsheet_id(spreadsheet_id)
        if not sid:
            return None
        return self._get_client().open_by_key(sid)

    def _get_activity_worksheet(self, spreadsheet_id=None):
        sid = self._resolve_spreadsheet_id(spreadsheet_id)
        cache_key = f"activity:{sid}"
        if cache_key in self._worksheet_cache:
            return self._worksheet_cache[cache_key]

        try:
            spreadsheet = self._get_spreadsheet(sid)
            if not spreadsheet:
                return None
            try:
                ws = spreadsheet.worksheet('Activity Log')
            except gspread.WorksheetNotFound:
                ws = spreadsheet.sheet1
                ws.update_title('Activity Log')

            if ws.row_values(1) != self.HEADERS:
                ws.update(range_name='A1:F1', values=[self.HEADERS])
                ws.format('A1:F1', {'textFormat': {'bold': True}})

            self._worksheet_cache[cache_key] = ws
            return ws
        except Exception as e:
            print(f"Google Sheets init error: {e}")
            return None

    def _get_users_worksheet(self, spreadsheet_id=None):
        sid = self._resolve_spreadsheet_id(spreadsheet_id)
        cache_key = f"users:{sid}"
        if cache_key in self._worksheet_cache:
            return self._worksheet_cache[cache_key]

        try:
            spreadsheet = self._get_spreadsheet(sid)
            if not spreadsheet:
                return None
            try:
                ws = spreadsheet.worksheet('Users')
            except gspread.WorksheetNotFound:
                ws = spreadsheet.add_worksheet(title='Users', rows=100, cols=10)
                ws.update(range_name='A1:G1', values=[self.USER_HEADERS])
                ws.format('A1:G1', {'textFormat': {'bold': True}})

            self._worksheet_cache[cache_key] = ws
            return ws
        except Exception as e:
            print(f"Google Sheets users worksheet error: {e}")
            return None

    def _get_blogs_worksheet(self, spreadsheet_id=None):
        sid = self._resolve_spreadsheet_id(spreadsheet_id)
        cache_key = f"blogs:{sid}"
        if cache_key in self._worksheet_cache:
            return self._worksheet_cache[cache_key]

        try:
            spreadsheet = self._get_spreadsheet(sid)
            if not spreadsheet:
                return None
            try:
                ws = spreadsheet.worksheet('Blogs')
            except gspread.WorksheetNotFound:
                ws = spreadsheet.add_worksheet(title='Blogs', rows=100, cols=10)
                ws.update(range_name='A1:H1', values=[self.BLOG_HEADERS])
                ws.format('A1:H1', {'textFormat': {'bold': True}})

            self._worksheet_cache[cache_key] = ws
            return ws
        except Exception as e:
            print(f"Google Sheets blogs worksheet error: {e}")
            return None

    def log_activity(self, user_name, action_type, action_text, blog_title="", details="", spreadsheet_id=None):
        try:
            ws = self._get_activity_worksheet(spreadsheet_id)
            if not ws:
                return False

            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            row = [timestamp, user_name, action_type, action_text, blog_title, details]
            ws.append_row(row, value_input_option='USER_ENTERED')
            return True
        except Exception as e:
            print(f"Google Sheets log error: {e}")
            self._worksheet_cache = {}
            return False

    def sync_user(self, uid, name, email, role, created_by="", created_at=None, last_login=None, spreadsheet_id=None):
        try:
            ws = self._get_users_worksheet(spreadsheet_id)
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

    def sync_blog(self, blog_id, title, status, category="", author_id="", created_at=None, updated_at=None, author_name="", spreadsheet_id=None):
        try:
            ws = self._get_blogs_worksheet(spreadsheet_id)
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

    @staticmethod
    def get_spreadsheet_id_for_user(user_id):
        try:
            from app.firebase.firestore_service import FirestoreService
            db = FirestoreService()
            settings = db.get_site_settings(user_id)
            user_id_val = settings.get('google_sheets_id', '').strip()
            if user_id_val:
                return user_id_val
        except Exception:
            pass
        return os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
