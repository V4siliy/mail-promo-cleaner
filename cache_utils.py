import hashlib
import json
import os
from datetime import datetime
from typing import Dict, List, Optional


def generate_message_id(sender: str, subject: str, email_datetime: int) -> str:
    """
    Generate a unique SHA256 hash from sender email, subject, and datetime.
    
    Args:
        sender: Email sender address
        subject: Email subject
        email_datetime: Email timestamp in milliseconds (Gmail internalDate)
    
    Returns:
        SHA256 hash as hexadecimal string
    """
    message_string = f"{sender}|{subject}|{email_datetime}"
    return hashlib.sha256(message_string.encode('utf-8')).hexdigest()


def get_email_date(email_datetime: int) -> str:
    """
    Convert Gmail internalDate (milliseconds) to date string in format DD.MM.YYYY.
    
    Args:
        email_datetime: Email timestamp in milliseconds
    
    Returns:
        Date string in format DD.MM.YYYY
    """
    dt = datetime.fromtimestamp(email_datetime / 1000)
    return dt.strftime("%d.%m.%Y")


def get_cache_path(email_date: str) -> str:
    """
    Get the cache file path for a given email date.
    
    Args:
        email_date: Date string in format DD.MM.YYYY
    
    Returns:
        Path to cache file
    """
    return f"data/cache/{email_date}/cache.json"


def load_cache(email_date: str) -> Dict[str, Dict]:
    """
    Load cache for a given email date.
    
    Args:
        email_date: Date string in format DD.MM.YYYY
    
    Returns:
        Dictionary with message IDs as keys and their data (email, subject) as values
    """
    cache_path = get_cache_path(email_date)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # If cache file is corrupted, return empty dict
            return {}
    return {}


def save_cache(email_date: str, cache_data: Dict[str, Dict]) -> None:
    """
    Save cache for a given email date.
    
    Args:
        email_date: Date string in format DD.MM.YYYY
        cache_data: Dictionary with message IDs as keys and their data as values
    """
    cache_path = get_cache_path(email_date)
    cache_dir = os.path.dirname(cache_path)
    
    # Create directory if it doesn't exist
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    # Save cache to file
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)


def is_message_handled(message_id: str, email_date: str) -> bool:
    """
    Check if a message has already been handled.
    
    Args:
        message_id: SHA256 hash of the message
        email_date: Date string in format DD.MM.YYYY
    
    Returns:
        True if message has been handled, False otherwise
    """
    cache = load_cache(email_date)
    return message_id in cache


def add_to_cache(message_id: str, email_date: str, sender: str, subject: str) -> None:
    """
    Add a message to the cache.
    
    Args:
        message_id: SHA256 hash of the message
        email_date: Date string in format DD.MM.YYYY
        sender: Email sender address
        subject: Email subject
    """
    cache = load_cache(email_date)
    cache[message_id] = {
        "email": sender,
        "subject": subject
    }
    save_cache(email_date, cache)
