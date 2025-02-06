import base64
import logging
import re
from typing import Dict, Union, List, Optional, Tuple

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from consultant import is_promo
from providers.gmail import GmailProvider

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)


def fetch_emails(gmail: Resource, page_token: Optional[str]) -> Tuple[List[Dict[str, Union[str, List[str]]]], Optional[str]]:
    try:
        results = gmail.users().messages().list(
            userId='me',
            labelIds=['UNREAD'],
            pageToken=page_token  # Include the page token in the request if there is one
        ).execute()
    except Exception as e:
        log.debug(f"Failed to fetch emails: {e}")
        return [], None

    messages: List[Dict[str, Union[str, List[str]]]] = results.get('messages', [])
    page_token = results.get('nextPageToken')
    return messages, page_token


def main():
    service = GmailProvider().create_service()
    page_token: Optional[str] = None
    total_pages_fetched = 0
    total_emails_deleted = 0

    while True:
        messages, page_token = fetch_emails(service, page_token)
        total_pages_fetched += 1
        log.debug(f"Fetched page {total_pages_fetched} of emails, deleted {total_emails_deleted}")

        for message in messages:
            email_data_parsed = parse_email_data(service, message)
            if is_promo(email_data_parsed):
                log.info(f'{email_data_parsed["subject"]} is promotional')
                try:
                    service.users().messages().trash(userId='me', id=message['id']).execute()
                    log.debug(">>>>>>>>>> Message Deleted to trash")
                    total_emails_deleted += 1
                except HttpError as e:
                    log.debug(f"Failed to delete email: {e}")
            else:
                try:
                    log.debug(f"Let's think about another logic")
                    # service.users().messages().modify(
                    #     userId='me',
                    #     id=message['id'],
                    #     body={'removeLabelIds': ['UNREAD']}).execute()
                except HttpError as e:
                    log.debug(f"Failed to delete email: {e}")
        if not page_token:
            break


def clean_body(text: str) -> str:
    cleaned_text = re.sub(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        'DELETED_LINK',
        text)
    cleaned_text = re.sub(r'\b\w{16,}\b', '', cleaned_text)
    return cleaned_text


def parse_email_data(
        gmail: Resource,
        message_info: Dict[str, Union[str, List[str]]]) -> Dict[str, Union[str, List[str]]]:
    try:
        msg = gmail.users().messages().get(
            userId='me',
            id=message_info['id'],
            format='full'
        ).execute()
    except Exception as e:
        log.exception(f"Failed to fetch email data: {e}")
        return {}
    try:
        headers = msg['payload']['headers']
        subject = next(header['value'] for header in headers if header['name'] == 'Subject')
        to = next(header['value'] for header in headers if header['name'] == 'To')
        sender = next(header['value'] for header in headers if header['name'] == 'From')
        cc = next((header['value'] for header in headers if header['name'] == 'Cc'), None)
    except Exception as e:
        log.exception(f"Failed to parse email data: {e}")
        return {}

    parts = msg['payload'].get('parts', [])
    for part in parts:
        if part['mimeType'] == 'text/plain':
            body = part['body'].get('data', '')
            body = base64.urlsafe_b64decode(body.encode('ASCII')).decode('utf-8')
            body = clean_body(body)
            break
    else:
        body = ''

    email_data_parsed: Dict[str, Union[str, List[str]]] = {
        'subject': subject,
        'to': to,
        'from': sender,
        'cc': cc,
        'labels': msg['labelIds'],
        'body': body,
    }
    return email_data_parsed


if __name__ == "__main__":
    main()
