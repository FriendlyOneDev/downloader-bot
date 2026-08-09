import os
import mimetypes
import glob
from telegram import InputMediaPhoto, InputMediaVideo

# Python 3.10's mimetypes has no .webp, and Instagram serves webp images.
mimetypes.add_type("image/webp", ".webp")

# Telegram bot upload limits (without local Bot API server)
TELEGRAM_PHOTO_LIMIT = 10 * 1024 * 1024
TELEGRAM_VIDEO_LIMIT = 50 * 1024 * 1024


class FileHandler:
    def __init__(self):
        self.file_path = os.getcwd()

    def _get_file_paths(self, file_name):
        pattern = os.path.join(self.file_path, f"*{file_name}*.*")
        return sorted(glob.glob(pattern))

    def get_files(self, file_name):
        files = self._get_file_paths(file_name)
        if not files:
            return [], []

        media_files = []
        skipped = []
        for file in files:
            mime_type, _ = mimetypes.guess_type(file)
            size = os.path.getsize(file)
            if mime_type and mime_type.startswith("image/"):
                if size > TELEGRAM_PHOTO_LIMIT:
                    skipped.append((os.path.basename(file), size))
                    continue
                media_files.append(InputMediaPhoto(media=open(file, "rb")))
            elif mime_type and mime_type.startswith("video/"):
                if size > TELEGRAM_VIDEO_LIMIT:
                    skipped.append((os.path.basename(file), size))
                    continue
                media_files.append(InputMediaVideo(media=open(file, "rb")))
            else:
                print(f"Unsupported file type: {file}")

        return media_files, skipped

    def delete_files(self, file_name):
        file_paths = self._get_file_paths(file_name)
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Deleted file: {path}")
                else:
                    print(f"File not found (skipped): {path}")
            except Exception as e:
                print(f"Error deleting file {path}: {e}")


if __name__ == "__main__":
    assert mimetypes.guess_type("x.webp")[0] == "image/webp"
    file_handler = FileHandler()
    print(file_handler._get_file_paths("Br-7zlEBjPc"))
