from instagrapi import Client
import os
import requests
from dotenv import load_dotenv

load_dotenv()


class InstagramHandler:
    def __init__(self):
        self.client = Client()

        username = os.getenv("INSTAGRAM_USERNAME")
        password = os.getenv("INSTAGRAM_PASSWORD")

        session_file = "instagrapi_session.json"

        # Try to load existing session
        try:
            self.client.load_settings(session_file)
        except:
            pass

        # Login
        if username and password:
            try:
                self.client.login(username, password)
                self.client.dump_settings(session_file)
            except Exception as e:
                print(f"Instagram login failed: {e}")

    def download_post(self, shortcode):
        media_pk = self.client.media_pk_from_code(shortcode)
        result = self.client.private_request(f"media/{media_pk}/info/")

        if result and "items" in result and len(result["items"]) > 0:
            item = result["items"][0]

            # Handle video (reel or video post)
            if "video_versions" in item and len(item["video_versions"]) > 0:
                video_url = item["video_versions"][0]["url"]
                self._download_file(video_url, f"{shortcode}.mp4")

            # Handle image
            elif "image_versions2" in item:
                candidates = item["image_versions2"].get("candidates", [])
                if candidates:
                    image_url = candidates[0]["url"]
                    self._download_file(image_url, f"{shortcode}.jpg")

            # Handle carousel (multiple images/videos)
            if "carousel_media" in item:
                for idx, media in enumerate(item["carousel_media"]):
                    if "video_versions" in media:
                        url = media["video_versions"][0]["url"]
                        self._download_file(url, f"{shortcode}_{idx + 1}.mp4")
                    elif "image_versions2" in media:
                        url = media["image_versions2"]["candidates"][0]["url"]
                        self._download_file(url, f"{shortcode}_{idx + 1}.jpg")

    def _download_file(self, url, filename):
        response = requests.get(url)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            f.write(response.content)


if __name__ == "__main__":
    handler = InstagramHandler()
    # https://www.instagram.com/reel/DRSErcyjOKX/?igsh=dWJxcHltZ2JtNjRl
    shortcode = "DRSErcyjOKX"
    handler.download_post(shortcode)
