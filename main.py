from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
from web_utils import LinkHandler
from file_utils import FileHandler
from download_utils.instagram_utils import InstagramHandler
from download_utils.tiktok_utils import fallback_download
import os


# init
load_dotenv()
api_key = os.getenv("telegram_token")
admin_id = int(os.getenv("admin_id"))

instagram_handler = InstagramHandler()
link_handler = LinkHandler()
file_handler = FileHandler()


async def handle_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    print(f"Received message: {text}")
    matches = link_handler.link_pattern.findall(text)
    print(f"Found matches: {matches}")
    for match in matches:
        try:
            shortcode = link_handler.extract_shortcode(match)
            print(f"Shortcode: {shortcode}")
            if "tiktok.com" in match:
                fallback_download(
                    match, shortcode, link_handler.extract_tiktok_type(match)
                )

            elif "instagram.com" in match:
                instagram_handler.download_post(shortcode)

            media = file_handler.get_files(shortcode)
            if media:
                await update.message.reply_media_group(media)
            else:
                print(f"No media files found for shortcode: {shortcode}")
        except Exception as e:
            print(f"Error processing {match}: {e}")
            await send_error_message(context, matches, str(e))
            return


async def send_error_message(context: ContextTypes.DEFAULT_TYPE, matches, error_msg=""):
    error_message = (
        "The following links could not be processed:\n"
        + "\n".join(matches)
        + "\n"
        + error_msg
    )
    await context.bot.send_message(chat_id=admin_id, text=error_message)


if __name__ == "__main__":
    app = ApplicationBuilder().token(api_key).build()

    app.add_handler(MessageHandler(filters.ALL, handle_links))

    app.run_polling()
