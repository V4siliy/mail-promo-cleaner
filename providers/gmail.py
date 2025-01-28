import os

from apiclient import discovery
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class GmailProvider:
    @classmethod
    def create_credentials(cls):
        scope = [
            "https://www.googleapis.com/auth/gmail.modify",
        ]
        credentials = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            credentials = Credentials.from_authorized_user_file("token.json", scope)
        # If there are no (valid) credentials available, let the user log in.
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", scope
                )
                credentials = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(credentials.to_json())

        return credentials

    @classmethod
    def create_service(cls):
        credentials = cls.create_credentials()
        return discovery.build("gmail", "v1", credentials=credentials)
