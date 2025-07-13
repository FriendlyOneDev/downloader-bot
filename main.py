from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
from urllib.parse import urlparse
import shutil
import time
import pyktok as pyk
import instaloader
import os
import re

# init
load_dotenv()
api_key = os.getenv("telegram_token")
loader = instaloader.Instaloader(
    download_comments=False,
    download_geotags=False,
    download_pictures=False,
    download_video_thumbnails=False,
    save_metadata=False,
)
LINK_REGEX = r"(https?://vm\.tiktok\.com/\S+/?|https?://www\.instagram\.com/reel/\S+/?(?:\?[^ \n]*)?)"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm alive.")


async def handle_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    matches = re.findall(LINK_REGEX, text)

    for match in matches:
        start_time = time.time()
        if "tiktok.com" in match:
            pyk.save_tiktok(match, save_video=True)
        elif "instagram.com/reel" in match:
            post = instaloader.Post.from_shortcode(
                loader.context, shortcode=extract_shortcode(match)
            )
            loader.download_post(post, target=extract_shortcode(match))

        time.sleep(1)

        video_file = get_newest_file(".mp4", since=start_time)
        if video_file:
            with open(video_file, "rb") as f:
                await update.message.reply_video(
                    f, reply_to_message_id=update.message.message_id
                )
            os.remove(video_file)

        if "instagram.com/reel" in match:
            folder_name = extract_shortcode(match)
            if os.path.isdir(folder_name):
                shutil.rmtree(folder_name)


def get_newest_file(extension=".mp4", since=None):
    newest_file = None
    newest_ctime = 0

    for root, _, files in os.walk("."):
        for file in files:
            if not file.endswith(extension):
                continue
            full_path = os.path.join(root, file)
            ctime = os.path.getctime(full_path)
            if since and ctime <= since:
                continue
            if ctime > newest_ctime:
                newest_ctime = ctime
                newest_file = full_path

    return newest_file


def extract_shortcode(url):
    path_parts = urlparse(url).path.strip("/").split("/")
    if len(path_parts) >= 2:
        return path_parts[1]
    raise ValueError("Invalid Instagram URL format.")


if __name__ == "__main__":
    app = ApplicationBuilder().token(api_key).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_links))

    app.run_polling()
