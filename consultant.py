import json
import os
import re
from datetime import datetime
from typing import Dict
import logging 

import anthropic
from anthropic import HUMAN_PROMPT, AI_PROMPT
from dotenv import load_dotenv
from ollama import chat
import tiktoken


load_dotenv()
log = logging.getLogger(__name__)

API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = os.getenv("ANTHROPIC_MODEL_NAME")
MAX_EMAIL_LEN = 3000
MAX_TOKENS = 3000


def extract_answer(text):
    pattern = r'<answer>(True|False)</answer>'
    match = re.search(pattern, text)
    if match:
        return match.group(1) == 'True'
    return False

def count_tokens(text, model="gpt-3.5-turbo"):
    encoder = tiktoken.encoding_for_model(model)
    return len(encoder.encode(text))

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)


client = anthropic.Anthropic(api_key=API_KEY)

config = load_config()

user_first_name = config["user_first_name"]
user_last_name = config["user_last_name"]

HOBBIES = "\n".join([f"{i+1}. {hobby}" for i, hobby in enumerate(config["hobbies"])])

NOT_DELETE = "\n".join([f"{i+1}. {item}" for i, item in enumerate(config["not_delete"])])


def is_promo(email_data, local_ollama=False):

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

    messages = [
        {"role": "user", "content": HUMAN_PROMPT + user_message['content']},
        {"role": "assistant", "content": AI_PROMPT}
    ]

    response = client.messages.count_tokens(
        model=MODEL,
        system=system_prompt,
        messages=messages
    )
    log.debug(response)

    response_data = response.model_dump_json()
    input_tokens = json.loads(response_data).get("input_tokens")
    log.info(f'tokens in request: {input_tokens}')

    if input_tokens > MAX_TOKENS:
        message = chat(model='llama3.1:8b', messages=[
          system_message,
          user_message,
        ])
        response = message.message.content
        output_tokens = count_tokens(response)
    else:
        message = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            temperature=0.0,
            system=system_prompt,
            messages=[user_message]
        )
        response = message.content[0].text
        output_tokens = message.usage.output_tokens
    
    log.info(f'tokens in response: {output_tokens}')
    current_date = datetime.now().strftime("%d.%m.%Y")
    response_filename = f"logs/{current_date}_response.csv"

    result = extract_answer(response)
    with open(response_filename, mode='a', newline='', encoding='utf-8') as f:
        f.write("\n\n============<email>============\n")
        f.write(f"{email_data['from']}, {email_data['subject']} is promotional: {result}")
        f.write(f"\n============<response: {'local llama' if local_ollama else 'Anthropic'}>============\n")
        f.write(f"\n============<TOKENS in: {input_tokens}, out: {output_tokens}>============\n")
        f.write(response)
    return result
