from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
from urllib.parse import urlparse
import time
import pyktok as pyk
import instaloader
import os
import re

# init
load_dotenv()
api_key = os.getenv("telegram_token")
instloader = instaloader.Instaloader(
    download_comments=False,
    download_geotags=False,
    download_pictures=False,
    download_video_thumbnails=False,
    save_metadata=False,
)
LINK_REGEX = r"(https?://vm\.tiktok\.com/\S+/?|https?://www\.instagram\.com/reel/\S+/?(?:\?[^ \n]*)?)"


async def handle_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    matches = re.findall(LINK_REGEX, text)

    for match in matches:
        start_time = time.time()

        if "tiktok.com" in match:
            pyk.save_tiktok(match, save_video=True)
        elif "instagram.com/reel" in match:
            shortcode = extract_shortcode(match)

            save_insta(match, shortcode)


def save_insta(shortcode):
    post = instaloader.Post.from_shortcode(instloader.context, shortcode)
    instloader.download_post(post, target=shortcode)


def extract_shortcode(url):
    path_parts = urlparse(url).path.strip("/").split("/")
    if len(path_parts) >= 2:
        return path_parts[1]
    raise ValueError("Invalid Instagram URL format.")


if __name__ == "__main__":
    app = ApplicationBuilder().token(api_key).build()

    app.add_handler(MessageHandler(filters.ALL, handle_links))

    app.run_polling()
