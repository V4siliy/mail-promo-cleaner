# Clean Your Gmail Inbox Effortlessly

`mail-promo-cleaner` is a Python-based script designed to declutter your Gmail inbox by filtering and deleting promotional emails while ensuring personal emails remain untouched.
It uses the Google Gmail API and advanced analysis logic to evaluate the nature of emails based on their content, sender, and context.

## Features

- Fetch emails from your Gmail inbox using the Gmail API.
- Analyze whether emails are promotional using DSPy-powered classification with OpenAI models.
- Class-based email classification with confidence scoring (65% threshold).
- Token-based email truncation for efficient processing.
- **Smart caching system** to prevent duplicate processing of personal messages:
  - Generates unique SHA256 IDs from sender email + subject + datetime
  - Stores handled personal messages in date-organized cache files
  - Automatically skips previously processed messages
- **Incremental processing mode** (`--stop-on-cache` flag) to only handle new messages
- Ensure personal or important emails, such as those related to hobbies or specific senders, are not filtered out.
- Automatically move promotional emails to the trash (promotional messages are not cached).
- Clear logs and analysis stored for transparency in outputs.
- Configurable email preferences for hobbies and email filtering criteria via `config.json`.

## Installation

### Prerequisites
1. Python 3.11+ installed on your system.
2. **Google API credentials** for accessing your Gmail using the Gmail API. Follow [Google API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python) for instructions on generating credentials (`credentials.json`).
3. **OpenAI API key** - Get your API key from [OpenAI](https://platform.openai.com/api-keys).
4. Install dependencies listed in the `pyproject.toml` file.

### Steps
1. Clone this repository:
   ```sh
   git clone https://github.com/V4siliy/mail-promo-cleaner.git
   cd gmail_promo_cleaner
   ```

2. Install dependencies:
   Run the following command in the root directory of your project, where the uv.lock file is present:

    ```sh
    uv install
    ```
    This command ensures that all the dependencies listed in uv.lock are installed in your environment with the specified versions.

3. Place your `credentials.json` in the root directory of the project.

4. Set up environment variables:
   Create a `.env` file in the root directory with:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL_NAME=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
   ```

5. Update your preferences in the `config.json` file:
   ```json
   {
       "user_first_name": "YourFirstName",
       "user_last_name": "YourLastName",
       "hobbies": ["Cycling", "Technology", "Financial planning"],
       "not_delete": ["Newsletter1", "ImportantSender"]
   }
   ```

## How to Use

1. **Run the Script**:
   Execute the script from the command line:
   ```sh
   # Normal mode: Process all unread emails, skipping previously handled ones
   python cleaner.py
   
   # Incremental mode: Stop when encountering first cached message (only process new messages)
   python cleaner.py --stop-on-cache
   ```

2. **Email Analysis**:
   - Emails are classified using DSPy-powered AI classification with confidence scoring.
   - Classification returns both a promotional flag (boolean) and confidence score (0.0-1.0).
   - Emails are considered promotional only if classified as promo AND confidence >= 65%.
   - Promotional emails are trashed (not deleted), while personal or important emails are preserved.
   - Personal messages are cached to prevent duplicate processing on subsequent runs.

3. **Caching System**:
   - Each personal message is assigned a unique SHA256 ID based on sender email + subject + datetime.
   - Cache files are organized by email date in `data/cache/{email_date}/cache.json`.
   - Previously handled personal messages are automatically skipped.
   - Promotional messages are not cached (they're deleted).

4. **Logs**:
   - Email classification results are logged under `logs/` in a CSV file format for verification.
   - Logs include SHA, email address, and subject for each processed message.

## Technical Overview

### Key Components
- **`fetch_emails(gmail, page_token)`**: Retrieves a list of unread emails using Gmail API.
- **`parse_email_data(gmail, message_info)`**: Extracts headers, body content, and internal date from an email.
- **`PromoEmailClassifier`**: Class-based email classifier using DSPy with OpenAI models.
  - Uses `EmailClassification` signature for structured output (promo: bool, confidence: float).
  - Implements token-based truncation for efficient processing.
- **`is_promo(email_data)`**: Determines if an email is promotional based on classification and 65% confidence threshold.
- **`cache_utils.py`**: Cache management module for preventing duplicate processing:
  - `generate_message_id()`: Creates unique SHA256 hash from sender + subject + datetime
  - `is_message_handled()`: Checks if a message was previously processed
  - `add_to_cache()`: Stores handled personal messages
  - Cache files organized by date: `data/cache/{email_date}/cache.json`

### Folder Structure
```plaintext
.
├── cleaner.py          # Main script to handle Gmail email cleaning
├── consultant.py       # Handles email analysis logic with DSPy and OpenAI
├── cache_utils.py      # Cache management for preventing duplicate processing
├── providers/
│   └── gmail.py        # Gmail API provider implementation
├── pyproject.toml      # Project metadata and requirements
├── config.json         # Configuration file for personalized settings
├── README.md           # Documentation file (this file)
├── uv.lock             # Dependency lockfile
├── logs/               # Stores analysis logs (format: DD.MM.YYYY_response.csv)
├── data/
│   └── cache/          # Cache files organized by email date
│       └── {email_date}/
│           └── cache.json  # Stores handled personal messages (SHA, email, subject)
├── .env                # Environment variables (OPENAI_API_KEY, etc.)
└── credentials.json    # Google API credentials (not in repo)
```

---

## Dependencies

Dependencies are managed via `pyproject.toml` and include:
- `dspy>=3.0.4`: DSPy framework for AI-powered classification.
- `google-api-python-client`: Gmail API interaction.
- `tiktoken`: Token counting and text truncation.
- `python-dotenv`: Environment variable management.
- `openai` (via DSPy): OpenAI API integration for email classification.

## Considerations and Limitations

- **API Quotas**: 
  - Deleting large numbers of emails in one session might hit your Gmail API usage quota.
  - OpenAI API usage will incur costs based on token consumption.
- **Email Safety**: Always review the filters in `config.json` to avoid accidental deletion of important emails.
- **Confidence Threshold**: Emails are only classified as promotional if both the classification is `promo=True` AND confidence >= 65%. This conservative approach helps protect important emails.
- **Token Limits**: Email bodies are automatically truncated based on token count (default: 3000 tokens) to stay within API limits.
- **Caching Behavior**:
  - Only personal messages are cached (promotional messages are deleted and not cached).
  - Cache prevents duplicate processing of personal messages across multiple runs.
  - Use `--stop-on-cache` flag for incremental processing (stops at first cached message).
  - Cache files are organized by email date for efficient lookup.

## Contribution

Contributions are welcome! Feel free to submit pull requests or report issues.

---

**Disclaimer**: Ensure you strictly adhere to Gmail's usage policies while using this script. The author is not responsible for any misuse or loss of data.

Happy Email Cleaning! ✉️