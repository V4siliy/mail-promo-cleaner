from ollama import chat
from ollama import ChatResponse

from typing import Dict
import re
from datetime import datetime
import json


def extract_answer(text):
    pattern = r'<answer>(True|False)</answer>'
    match = re.search(pattern, text)
    if match:
        return match.group(1) == 'True'
    return False


def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)


config = load_config()

user_first_name = config["user_first_name"]
user_last_name = config["user_last_name"]

HOBBIES = "\n".join([f"{i+1}. {hobby}" for i, hobby in enumerate(config["hobbies"])])

NOT_DELETE = "\n".join([f"{i+1}. {item}" for i, item in enumerate(config["not_delete"])])

MAX_EMAIL_LEN = 3000


def is_promo(email_data):

    system_prompt = f"""You are an AI assistant tasked with managing the mail inbox of a busy individual named 
    {user_first_name} {user_last_name}. 
    Your primary goal is to filter out promotional emails from their personal account while ensuring that 
    important personal communications are not ignored.

    You will work with information from email:
    <to></to>
    <from></from>
    <cc>/<cc>
    <subject></subject>
    <labels></labels>
    <body>first {MAX_EMAIL_LEN} symbols</body>

    {user_first_name}'s hobbies and interests include:
    <hobbies>
    {HOBBIES}
    </hobbies>
    
    <not_delete>
    {NOT_DELETE}
    </not_delete>

    Your task is to determine whether this <email> should be marked as promotional (True) or personal (False). 
    Follow these guidelines:
    
    1. Label  Analysis:
      - All meassage with IMPORTANT label should be marked as personal (False)
      
    2. Sender Analysis:
       - If the sender is a known person, especially a family member (with the same last name), a close acquaintance, 
       or a potential contact {user_first_name} might be interested in, lean towards marking it as personal.
       - If the email is related with one record from <not_delete> list - mark it as personal (False)
    
    3. Content Analysis:
       - Look for promotional indicators such as offers, discounts, marketing language, or automated content.
       - Check the same promotional content in Russian, Serbian or other languages.
       - Identify if the email is mass-sent or from a non-essential mailing list.
       - Consider if the email addresses {user_first_name} by name or contains personal context.
    
    4. Action Requirements:
       - If the email requires action on important matters (e.g., sending a payment or invoice details), mark it as personal.
       - Ignore requests for non-essential actions like purchasing discounted items or signing up for rewards programs.
    
    5. Interest Relevance:
       - Consider if the email content relates to {user_first_name}'s hobbies or interests, even if it's promotional in nature.
    
    6. Caution:
       - If there's any doubt about whether an email is promotional or personal, err on the side of marking it as personal (False).
    
    Before providing your final decision, wrap your analysis inside <email_analysis> tags. Consider the following:
    - Categorize the email into a specific type (e.g., personal communication, promotional offer, newsletter, etc.)
    - List out specific promotional indicators found in the email
    - List out personal elements or context found in the email
    - The sender's relationship to {user_first_name}
    - The content of the email and its purpose
    - Whether the email requires important action
    - Explicitly consider each of {user_first_name}'s hobbies and interests in relation to the email content
    It's OK for this section to be quite long.

    Finally, decide is email promotional, then response only with one word in <answer>: 
    - write 'True' for promotional emails that should be filtered, 
    - write 'False' for personal emails that should not be filtered.
    
    <answer> is mandatory
    """

    system_message: Dict[str, str] = {
      "role": "system",
      "content": system_prompt
    }

    truncated_body = email_data['body'][:MAX_EMAIL_LEN] + ("..." if len(email_data['body']) > MAX_EMAIL_LEN else "")

    user_message: Dict[str, str] = {
        "role": "user",
        "content": (
            "Here is the email you need to analyze:\n\n"
            "<email>\n"
            f"Subject: {email_data['subject']}\n"
            f"To: {email_data['to']}\n"
            f"From: {email_data['from']}\n"
            f"Cc: {email_data['cc']}\n"
            f"Gmail labels: {email_data['labels']}\n"
            f"Body: {truncated_body}"
            "</email>\n"
        )
    }

    response: ChatResponse = chat(model='llama3.1:8b', messages=[
      system_message,
      user_message,
    ])
    current_date = datetime.now().strftime("%d.%m.%Y")
    response_filename = f"logs/{current_date}_response.csv"

    result = extract_answer(response.message.content)
    with open(response_filename, mode='a', newline='', encoding='utf-8') as f:
        f.write("\n\n============<email>============\n")
        f.write(f"{email_data['from']}, {email_data['subject']} is promotional: {result}")
        f.write("\n============<response>============\n")
        f.write(response.message.content)
    return result
