import json
import logging
import os
from datetime import datetime
from typing import Dict, Tuple

import dspy
import tiktoken
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
MAX_TOKENS = 3000
CONFIDENCE_THRESHOLD = 0.65  # 65% threshold


def count_tokens(text, model="gpt-3.5-turbo"):
    encoder = tiktoken.encoding_for_model(model)
    return len(encoder.encode(text))


def truncate_by_tokens(text: str, max_tokens: int, model: str = "gpt-3.5-turbo") -> str:
    """
    Truncate text to fit within a maximum token count.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens allowed
        model: Model name for token encoding
    
    Returns:
        Truncated text with "..." appended if truncation occurred
    """
    encoder = tiktoken.encoding_for_model(model)
    tokens = encoder.encode(text)
    
    if len(tokens) <= max_tokens:
        return text
    
    # Truncate to max_tokens and decode back to text
    truncated_tokens = tokens[:max_tokens]
    truncated_text = encoder.decode(truncated_tokens)
    return truncated_text + "..."

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)


# Initialize DSPy with OpenAI
lm = dspy.LM(model=MODEL, api_key=API_KEY)
dspy.configure(lm=lm)

config = load_config()

user_first_name = config["user_first_name"]
user_last_name = config["user_last_name"]

HOBBIES = "\n".join([f"{i+1}. {hobby}" for i, hobby in enumerate(config["hobbies"])])

NOT_DELETE = "\n".join([f"{i+1}. {item}" for i, item in enumerate(config["not_delete"])])


# DSPy signature for email classification
class EmailClassification(dspy.Signature):
    """Classify an email as promotional or personal. Return promo (boolean) and confidence (float 0-1)."""
    
    email_info: str = dspy.InputField(desc="Email information including subject, from, to, cc, labels, and body")
    user_context: str = dspy.InputField(desc="User's name, hobbies, and items that should not be deleted")
    guidelines: str = dspy.InputField(desc="Guidelines for classification")
    
    promo: bool = dspy.OutputField(desc="True if email is promotional, False if personal")
    confidence: float = dspy.OutputField(desc="Confidence score between 0.0 and 1.0")


class PromoEmailClassifier:
    """Class-based email classifier using DSPy."""
    
    def __init__(self):
        self.classify = dspy.ChainOfThought(EmailClassification)
        self._build_guidelines()
    
    def _build_guidelines(self):
        """Build classification guidelines based on user config."""
        self.guidelines = f"""You are an AI assistant tasked with managing the mail inbox of a busy individual named 
{user_first_name} {user_last_name}. 
Your primary goal is to filter out promotional emails from their personal account while ensuring that 
important personal communications are not ignored.

Follow these guidelines:

1. Label Analysis:
  - All messages with IMPORTANT label should be marked as personal (False)
  
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
  - Provide a confidence score based on how certain you are about the classification (0.0 to 1.0)."""
    
    def classify_email(self, email_data: Dict) -> Tuple[bool, float]:
        """
        Classify an email as promotional or personal.
        
        Args:
            email_data: Dictionary containing email information (subject, from, to, cc, labels, body)
        
        Returns:
            Tuple of (promo: bool, confidence: float)
        """
        # Build the base email info structure (without body) to calculate its token count
        base_email_info = (
            f"Subject: {email_data['subject']}\n"
            f"To: {email_data['to']}\n"
            f"From: {email_data['from']}\n"
            f"Cc: {email_data.get('cc', 'N/A')}\n"
            f"Gmail labels: {email_data['labels']}\n"
            f"Body: "
        )
        
        # Calculate tokens used by base structure
        base_tokens = count_tokens(base_email_info, MODEL)
        
        # Calculate available tokens for body (leave some buffer for the rest of the prompt)
        # Reserve tokens for user_context, guidelines, and DSPy overhead
        available_tokens_for_body = max(0, MAX_TOKENS - base_tokens - 500)  # 500 token buffer
        
        # Truncate body based on available tokens
        truncated_body = truncate_by_tokens(email_data['body'], available_tokens_for_body, MODEL)
        
        email_info = base_email_info + truncated_body
        
        user_context = (
            f"User: {user_first_name} {user_last_name}\n"
            f"Hobbies and interests:\n{HOBBIES}\n\n"
            f"Items that should not be deleted:\n{NOT_DELETE}"
        )
        
        try:
            result = self.classify(
                email_info=email_info,
                user_context=user_context,
                guidelines=self.guidelines
            )
            
            # Extract promo and confidence from result
            promo = result.promo if isinstance(result.promo, bool) else str(result.promo).lower() == 'true'
            confidence = float(result.confidence) if isinstance(result.confidence, (int, float)) else float(str(result.confidence))
            
            # Ensure confidence is in valid range
            confidence = max(0.0, min(1.0, confidence))
            
            log.info(f"Classification result: promo={promo}, confidence={confidence:.2f}")
            
            return promo, confidence
            
        except Exception as e:
            log.error(f"Error during classification: {e}")
            # Default to personal (False) with low confidence on error
            return False, 0.0


# Initialize the classifier
classifier = PromoEmailClassifier()


def is_promo(email_data: Dict, local_ollama: bool = False) -> bool:
    """
    Determine if an email is promotional based on classification and confidence threshold.
    
    Args:
        email_data: Dictionary containing email information
        local_ollama: Unused parameter (kept for backward compatibility)
    
    Returns:
        True if email is promotional (and confidence >= threshold), False otherwise
    """
    promo, confidence = classifier.classify_email(email_data)
    
    # Log the classification
    current_date = datetime.now().strftime("%d.%m.%Y")
    response_filename = f"logs/{current_date}_response.csv"

    if not os.path.exists(os.path.dirname(response_filename)):
        os.makedirs(os.path.dirname(response_filename))
    # Determine final decision based on confidence threshold
    is_promotional = promo and confidence >= CONFIDENCE_THRESHOLD
    
    with open(response_filename, mode='a', newline='', encoding='utf-8') as f:
        f.write("\n\n============<email>============\n")
        f.write(f"{email_data['from']}, {email_data['subject']}\n")
        f.write(f"Classification: promo={promo}, confidence={confidence:.2f}, threshold={CONFIDENCE_THRESHOLD}\n")
        f.write(f"Final decision: {'PROMOTIONAL' if is_promotional else 'PERSONAL'}\n")
        f.write(f"============<response: DSPy>============\n")
    
    log.info(f"Email from {email_data['from']} classified as {'PROMOTIONAL' if is_promotional else 'PERSONAL'} "
             f"(promo={promo}, confidence={confidence:.2f})")
    
    return is_promotional
