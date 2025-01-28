# Clean Your Gmail Inbox Effortlessly

`mail-promo-cleaner` is a Python-based script designed to declutter your Gmail inbox by filtering and deleting promotional emails while ensuring personal emails remain untouched.
It uses the Google Gmail API and advanced analysis logic to evaluate the nature of emails based on their content, sender, and context.

## Features

- Fetch emails from your Gmail inbox using the Gmail API.
- Analyze whether emails are promotional using detailed content-based logic enriched by local llama:8b assistant.
- Ensure personal or important emails, such as those related to hobbies or specific senders, are not filtered out.
- Automatically move promotional emails to the trash.
- Clear logs and analysis stored for transparency in outputs.
- Configurable email preferences for hobbies and email filtering criteria via `config.json`.

## Installation

### Prerequisites
1. Python 3.10+ installed on your system.
2. **Google API credentials** for accessing your Gmail using the Gmail API. Follow [Google API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python) for instructions on generating credentials (`credentials.json`).
3. Install dependencies listed in the `pyproject.toml` file.

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

4. Update your preferences in the `config.json` file:
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
   python cleaner.py
   ```

2. **Email Analysis**:
   - Emails are classified based on their labels, sender details, and content relevance.
   - Promotional emails are trashed (not deleted), while personal or important emails are marked as read.

3. **Logs**:
   - Email classification results are logged under `logs/` in a CSV file format for verification.

## Technical Overview

### Key Functions
- **`fetch_emails(gmail, page_token)`**: Retrieves a list of unread emails using Gmail API.
- **`parse_email_data(gmail, message_info)`**: Extracts headers and body content from an email.
- **`is_promo(email_data)`**: Uses llama to classify the email as promotional or personal.

### Folder Structure
```plaintext
.
├── cleaner.py          # Main script to handle Gmail email cleaning
├── consultant.py       # Handles email analysis logic with OpenAI
├── pyproject.toml      # Project metadata and requirements
├── config.json         # Configuration file for personalized settings
├── README.md           # Documentation file (this file)
├── uv.lock             # Dependency lockfile
├── logs/               # Stores analysis logs
```

---

## Dependencies

Dependencies are managed via `pyproject.toml` and include:
- `google-api-python-client`: Gmail API interaction.
- `ollama`: Advanced classification using AI.

## Considerations and Limitations

- **API Quotas**: Deleting large numbers of emails in one session might hit your API usage quota.
- **Email Safety**: Always review the filters in `config.json` to avoid accidental deletion of important emails.

## Contribution

Contributions are welcome! Feel free to submit pull requests or report issues.

---

**Disclaimer**: Ensure you strictly adhere to Gmail's usage policies while using this script. The author is not responsible for any misuse or loss of data.

Happy Email Cleaning! ✉️