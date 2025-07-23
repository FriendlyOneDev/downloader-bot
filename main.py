from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.request import HTTPXRequest
from dotenv import load_dotenv
from web_utils import LinkHandler
from file_utils import FileHandler
from download_utils.instagram_utils import InstagramHandler
from download_utils.tiktok_utils import fallback_download
from stats_utils import load_stats, save_stats, hash_id
import os


# Load environment variables
stats = load_stats()  # Just to show off bot's usage B)
load_dotenv()
api_key = os.getenv("telegram_token")
admin_id = int(os.getenv("admin_id"))

# Initialize handlers
instagram_handler = InstagramHandler()
link_handler = LinkHandler()
file_handler = FileHandler()


# Main function to handle incoming messages, extracting links, and processing them
async def handle_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text
    print(f"Received message: {text}")
    matches = link_handler.link_pattern.findall(text)
    print(f"Found matches: {matches}")

    # Process each matched link
    for match in matches:
        # Add new unique user and chat to stats(without saving to file)
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id

        # Hash user and chat IDs for privacy
        user_hash = hash_id(user_id)
        chat_hash = hash_id(chat_id)

        if user_id not in stats["unique_users"]:
            stats["unique_users"].add(user_hash)
        if chat_id not in stats["unique_chats"]:
            stats["unique_chats"].add(chat_hash)

        try:
            shortcode = link_handler.extract_shortcode(match)
            print(f"Shortcode: {shortcode}")

            # Service-specific handling and downloading
            if "tiktok.com" in match:
                fallback_download(
                    match, shortcode, link_handler.extract_tiktok_type(match)
                )
            elif "instagram.com" in match:
                instagram_handler.download_post(shortcode)

            # Getting and sending media files
            media = file_handler.get_files(shortcode)
            if media:
                await update.message.reply_media_group(media)

                # Cleanup after sending media
                try:
                    file_handler.delete_files(shortcode)
                except Exception as e:

                    # Cleanup failed, notify admin
                    print(f"Error deleting files for {shortcode}: {e}")
                    await send_error_message(context, [match], f"Cleanup failed: {e}")
            else:
                # No media files found, notify user and admin
                user_msg = "Something went wrong while retrieving media for this link."
                await update.message.reply_text(user_msg)
                await send_error_message(context, [match], "No media files found.")

            # Saving stats
            stats["total_links"] += 1
            save_stats(stats)
        except Exception as e:
            # Exception caught, notify user and admin
            print(f"Error processing {match}: {e}")
            await update.message.reply_text(
                "Something went wrong while processing the link."
            )
            await send_error_message(context, [match], str(e))


# Function to send error messages to the admin
async def send_error_message(context: ContextTypes.DEFAULT_TYPE, matches, error_msg=""):
    error_message = (
        "The following links could not be processed:\n"
        + "\n".join(matches)
        + "\n"
        + error_msg
    )
    await context.bot.send_message(chat_id=admin_id, text=error_message)


if __name__ == "__main__":
    # Bot setup and start polling
    request = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=10.0,
        media_write_timeout=60.0,
    )

    app = ApplicationBuilder().token(api_key).request(request).build()

    app.add_handler(MessageHandler(filters.ALL, handle_links))

    app.run_polling()
