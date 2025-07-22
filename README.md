# Telegram Media Downloader Bot

A Telegram bot that detects Instagram and TikTok links in messages, downloads the associated media, and sends them back as albums (media groups) to the user. Includes error reporting and automatic cleanup of downloaded files.

---

## Features

- Supports downloading posts from Instagram and TikTok links.
- Automatically detects media files (images/videos) associated with a link.
- Sends media as Telegram media groups.
- Error handling with user notifications and admin alerts.
- Automatic cleanup of downloaded media files after sending.

---

## Setup

### Prerequisites

- Python 3.9+
- Telegram Bot Token (create a bot with [@BotFather](https://t.me/BotFather))
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) library
- Other dependencies (listed in `requirements.txt`)

### Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/telegram-media-downloader-bot.git
cd telegram-media-downloader-bot
```

2. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```
3. Install dependencies:
```
pip install -r requirements.txt
```
4. Create a .env file with your credentials:
```
telegram_token=YOUR_TELEGRAM_BOT_TOKEN
admin_id=YOUR_TELEGRAM_USER_ID
```
5. Run the bot




