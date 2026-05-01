from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler
)
from telegram.error import RetryAfter, BadRequest, NetworkError
from telegram.request import HTTPXRequest
from dotenv import load_dotenv
from web_utils import LinkHandler
from file_utils import FileHandler
from download_utils.instagram_utils import InstagramHandler
from download_utils.tiktok_utils import fallback_download
from stats_utils import load_stats, save_stats, hash_id
from datetime import datetime
import asyncio
import os
import glob


def _is_too_large_error(exc: Exception) -> bool:
    return "too large" in str(exc).lower()


async def send_media_group_with_retry(message, media_batch, max_retries=4):
    """Send a media group, retrying on Telegram flood control."""
    for attempt in range(max_retries):
        try:
            return await message.reply_media_group(media_batch)
        except RetryAfter as e:
            wait = getattr(e, "retry_after", 5) + 1
            print(f"Flood control: waiting {wait}s (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(wait)
        except (BadRequest, NetworkError) as e:
            if _is_too_large_error(e):
                raise
            if attempt + 1 == max_retries:
                raise
            print(f"Transient send error ({e}); retrying in 2s")
            await asyncio.sleep(2)
    raise RuntimeError("send_media_group_with_retry: retries exhausted")


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

    # Admin-only: retry Instagram login via plain text
    if text.strip().lower() == "login" and update.message.from_user.id == admin_id:
        await update.message.reply_text("Retrying Instagram login...")
        instagram_handler._try_login()
        if instagram_handler.logged_in:
            await update.message.reply_text("Instagram: logged in successfully")
        else:
            await update.message.reply_text(f"Instagram: login failed\n{instagram_handler.login_error}")
        return

    matches = link_handler.link_pattern.findall(text)

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
            media, skipped = file_handler.get_files(shortcode)

            if media or skipped:
                if skipped:
                    skipped_lines = "\n".join(
                        f"- {name} ({size // (1024 * 1024)} MB)" for name, size in skipped
                    )
                    await update.message.reply_text(
                        "Some files exceeded Telegram's upload limit "
                        "(50 MB video / 10 MB photo) and were skipped:\n" + skipped_lines
                    )
                    await send_error_message(
                        context, [match], f"Skipped oversized files:\n{skipped_lines}"
                    )

                rejected_too_large = False
                # Telegram limits media groups to 10 items
                for i in range(0, len(media), 10):
                    try:
                        await send_media_group_with_retry(
                            update.message, media[i:i + 10]
                        )
                    except (BadRequest, NetworkError) as e:
                        if _is_too_large_error(e):
                            rejected_too_large = True
                            print(f"Telegram rejected batch as too large: {e}")
                        else:
                            raise
                    # Pace batches to avoid hitting flood control on long carousels
                    if i + 10 < len(media):
                        await asyncio.sleep(1)

                if rejected_too_large:
                    await update.message.reply_text(
                        "Telegram rejected one of the files as too large to deliver."
                    )

                # Cleanup after sending media (and any skipped leftovers)
                try:
                    file_handler.delete_files(shortcode)
                except Exception as e:

                    # Cleanup failed, notify admin
                    print(f"Error deleting files for {shortcode}: {e}")
                    await send_error_message(context, [match], f"Cleanup failed: {e}")
            else:
                # No media files found, notify user and admin
                print(f"No media on disk for shortcode {shortcode} ({match})")
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

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pong!")


def cleanup_media_files():
    extensions = ("*.mp4", "*.jpg", "*.jpeg", "*.png")
    removed = 0
    for ext in extensions:
        for f in glob.glob(os.path.join(os.getcwd(), ext)):
            os.remove(f)
            removed += 1
    if removed:
        print(f"Startup cleanup: removed {removed} leftover media file(s)")

async def on_startup(app):
    cleanup_media_files()
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ig_status = "logged in" if instagram_handler.logged_in else "NOT logged in"
    await app.bot.send_message(
        chat_id=admin_id,
        text=f"Bot started at {start_time}\nInstagram: {ig_status}"
    )

if __name__ == "__main__":
    # Bot setup and start polling
    request = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=10.0,
        media_write_timeout=60.0,
    )

    app = (ApplicationBuilder()
           .token(api_key)
           .request(request)
           .post_init(on_startup)
           .build())

    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(MessageHandler(filters.ALL, handle_links))

    app.run_polling()
