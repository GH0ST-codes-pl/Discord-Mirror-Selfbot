# Discord Mirror Selfbot

A lightweight Discord selfbot built with `discord.py-self` to mirror messages from a specific channel to a webhook destination. It includes a message reporting feature and supports attachments, replies, and timestamps.

> [!WARNING]
> **Selfbot Disclaimer:** Using selfbots is against Discord's Terms of Service and can lead to your account being banned. Use at your own risk.

## Features
- **Real-time Mirroring:** Forwards messages from a source channel to a destination webhook.
- **Attachment Support:** Mirrors images and files attached to messages.
- **Reply Tracking:** Shows who was being replied to in the forwarded message.
- **Message Reporting:** Simple `!report <message_id>` command to send detailed message info to a separate review webhook.
- **Clean Formatting:** Uses Discord timestamps to preserve the original message time.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/discord-mirror-selfbot.git
   cd discord-mirror-selfbot
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Open `.env` and fill in your details:
     - `SECRET_TOKEN`: Your Discord user token.
     - `SOURCE_ID`: The ID of the channel you want to mirror from.
     - `WEBHOOK_URL`: The destination webhook URL.
     - `REPORT_WEBHOOK_URL`: The webhook URL where reports will be sent.

## Usage

Run the bot:
```bash
python main.py
```

### Commands
- `!report <message_id>`: Send a detailed report of the specified message to the report webhook. Run this in the source channel.

## License
MIT License - see [LICENSE](LICENSE) for details.
