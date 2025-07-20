from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
from web_utils import LinkHandler
from downloading_utils.instagram_utils import InstagramHandler
import pyktok as pyk
import os


# init
load_dotenv()
api_key = os.getenv("telegram_token")
instagram_handler = InstagramHandler()
link_handler = LinkHandler()


async def handle_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    print(f"Received message: {text}")
    matches = link_handler.link_pattern.findall(text)
    print(f"Found matches: {matches}")
    for match in matches:
        shortcode = link_handler.extract_shortcode(match)
        print(f"Shortcode: {shortcode}")
        if "tiktok.com" in match:
            pyk.save_tiktok(match, save_video=True)
        elif "instagram.com/reel" in match:
            pass


if __name__ == "__main__":
    app = ApplicationBuilder().token(api_key).build()

    app.add_handler(MessageHandler(filters.ALL, handle_links))

    app.run_polling()
