from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
import time
import pyktok as pyk
import os
import re

# init
load_dotenv()
api_key = os.getenv("telegram_token")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm alive.")


async def handle_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    matches = re.findall(r"https?://vm\.tiktok\.com/\S+/?", text)

    for match in matches:
        start_time = time.time()
        pyk.save_tiktok(match, save_video=True)

        time.sleep(1)

        video_file = get_newest_file(".mp4", since=start_time)
        if video_file:
            with open(video_file, "rb") as f:
                await update.message.reply_video(
                    f, reply_to_message_id=update.message.message_id
                )
            os.remove(video_file)


def get_newest_file(extension=".mp4", since=None):
    files = [f for f in os.listdir(".") if f.endswith(extension)]
    if since:
        files = [f for f in files if os.path.getctime(f) > since]
    if not files:
        return None
    return max(files, key=os.path.getctime)


if __name__ == "__main__":
    app = ApplicationBuilder().token(api_key).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_links))

    app.run_polling()
