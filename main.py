from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
from urllib.parse import urlparse
from web_utils import instaloader_init, LinkHandler
import pyktok as pyk
import os
import instaloader


# init
load_dotenv()
api_key = os.getenv("telegram_token")
instagram_downloader = instaloader_init()
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
            post = instaloader.Post.from_shortcode(
                instagram_downloader.context, shortcode
            )
            instagram_downloader.download_post(post, target=shortcode)


if __name__ == "__main__":
    app = ApplicationBuilder().token(api_key).build()

    app.add_handler(MessageHandler(filters.ALL, handle_links))

    app.run_polling()
