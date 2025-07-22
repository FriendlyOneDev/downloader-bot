# Telegram Media Downloader Bot

A Telegram bot that detects Instagram and TikTok links in messages, downloads the associated media, and sends them back as albums (media groups) to the user. Includes error reporting and automatic cleanup of downloaded files.

---

## Features

- Supports downloading posts from Instagram and TikTok links.
- Sends downloaded media as Telegram media groups.
- Automatic cleanup of downloaded media files after sending.

---

## Setup
### Installation

1. Clone the repository:
```
git clone https://github.com/FriendlyOneDev/downloader-bot
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
admin_id=YOUR_TELEGRAM_USER_ID #Bot needs it to send error messages directly to you. You can tweak the code to not require this
```
5. Run the bot




