from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

class GoogleCalendar:
    SCOPES = [os.getenv('SCOPES')]
    FILE_PATH = os.getenv('FILE_PATH')

    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            filename=self.FILE_PATH, scopes=self.SCOPES
        )
        self.service = build('calendar', 'v3', credentials=credentials)

    def get_calendar_list(self):
        return self.service.calendarList().list().execute()

    def add_calendar_(self, calendar_id):
        calendar_list_entry = {
            'id': calendar_id
        }

        return self.service.calendarList().insert(
            body=calendar_list_entry).execute()

    def add_event(self, calendar_id, body):
        return self.service.events().insert(
            calendarId=calendar_id,
            body=body).execute()

    def delete_event(self, calendar_id, eventId):
        self.service.events().delete(calendarId=calendar_id, eventId=eventId).execute()

    def get_events(self, calendar_id):
        return self.service.events().list(calendarId=calendar_id, pageToken=None).execute()