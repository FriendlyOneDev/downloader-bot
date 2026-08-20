from instagrapi import Client
import instaloader
import os
import requests
import time
import yt_dlp
from dotenv import load_dotenv

from download_utils import snapsave_utils

load_dotenv()


class InstagramHandler:
    SESSION_FILE = "instagrapi_session.json"
    COOKIES_FILE = os.getenv("INSTAGRAM_COOKIES", "instagram_cookies.txt")

    # Logging in is opt-in: the logged-out methods cover everything, and
    # automated logins are what earn the account scraping warnings and bans.
    LOGIN_ENABLED = os.getenv("INSTAGRAM_LOGIN", "").lower() in ("1", "true", "yes")

    def __init__(self):
        self.client = Client()
        self.logged_in = False
        self.login_error = None
        self._configure_client()
        if self.LOGIN_ENABLED:
            self._try_login()
        else:
            print("Instagram: login disabled (set INSTAGRAM_LOGIN=1 to enable)")

        # Instaloader fallback (no login, works for public posts)
        self.loader = instaloader.Instaloader(
            download_comments=False,
            download_geotags=False,
            download_video_thumbnails=False,
            save_metadata=False,
            post_metadata_txt_pattern="",
            dirname_pattern=".",
        )

    def _try_login(self, force=False):
        """Attempt to log in, reusing session if available.

        force=True discards any stored session and logs in from scratch. Only
        the admin 'login' command should force, since a fresh login can trigger
        a challenge that has to be approved in the Instagram app.
        """
        self.logged_in = False
        self.login_error = None

        username = os.getenv("INSTAGRAM_USERNAME")
        password = os.getenv("INSTAGRAM_PASSWORD")

        # Try to reuse existing session
        has_session = (
            os.path.isfile(self.SESSION_FILE)
            and os.path.getsize(self.SESSION_FILE) > 0
        )
        if has_session and not force:
            try:
                self.client.load_settings(self.SESSION_FILE)
                self._configure_client()
                self.client.login(username, password)
                self.client.user_info_by_username(username)
                self.logged_in = True
                self.client.dump_settings(self.SESSION_FILE)
                print("Instagram: session is valid")
                return
            except Exception as e:
                print(f"Instagram: session reuse failed ({e})")
                self.login_error = str(e)
                # Don't attempt fresh login automatically -
                # it triggers a new challenge creating an infinite loop.
                # Use the 'login' command after approving on Instagram.
                return

        if force and has_session:
            # A stale session poisons every later attempt, so drop it and
            # start from a clean client.
            try:
                os.remove(self.SESSION_FILE)
                print("Instagram: discarded stale session file")
            except OSError as e:
                print(f"Instagram: could not remove session file ({e})")
            self.client = Client()
            self._configure_client()

        # Fresh login
        if username and password:
            try:
                self.client.login(username, password)
                self.client.dump_settings(self.SESSION_FILE)
                self.logged_in = True
                print("Instagram: fresh login successful")
            except Exception as e:
                self.login_error = str(e)
                print(f"Instagram login failed: {e}")
        else:
            self.login_error = "INSTAGRAM_USERNAME/INSTAGRAM_PASSWORD not set"
            print(f"Instagram: {self.login_error}")

    def _configure_client(self):
        """Configure client with updated Instagram app version to avoid checkpoint."""
        self.client.set_settings({
            "app_version": "410.0.0.30.115",
            "android_version": 34,
            "android_release": "14.0.0",
            "version_code": "640000000"
        })
        self.client.set_user_agent(
            "Instagram 410.0.0.30.115 Android (34/14.0.0; 640dpi; 1440x3040; samsung; SM-G998B; p3s; exynos2100; en_US; 640000000)"
        )

    def download_post(self, shortcode, max_retries=2):
        """Download post, trying each available method in order."""
        errors = []

        # Logged-out methods first - they cost the account nothing. snapsave
        # before instagrapi because it reaches restricted posts without
        # putting the account anywhere near Instagram's scraping detection.
        methods = [
            self._download_ytdlp,
            self._download_instaloader,
            self._download_snapsave,
        ]
        if self.logged_in:
            methods.append(self._download_instagrapi)

        # Every method pulls from the same Instagram CDN, so one round of
        # timeouts or 429s knocks out all of them at once. Same retry shape as
        # tiktok_utils.fallback_download.
        for attempt in range(max_retries):
            if attempt:
                time.sleep(3 * attempt)
                print(f"Instagram retry {attempt}/{max_retries - 1} for {shortcode}")
            errors = []
            for method in methods:
                name = method.__name__.lstrip("_")
                try:
                    method(shortcode)
                    return
                except Exception as e:
                    errors.append(f"{name}: {e}")
                    print(f"{name} failed: {e}")

        raise RuntimeError(self._failure_message(errors))

    @staticmethod
    def _trim(text, limit=160):
        text = " ".join(str(text).split())
        return text if len(text) <= limit else text[:limit] + "..."

    def _failure_message(self, errors):
        detail = "; ".join(self._trim(e) for e in errors) or "no download method ran"

        # Instagram returns 'geoblock_required' for any audience restriction,
        # not just geographic ones - an age limit ("people under 25 can't see
        # this content") reports the same code. Logged-out fallbacks always
        # fail these, so name the restriction instead of blaming whichever
        # fallback happened to die last.
        if any("geoblock" in e.lower() for e in errors):
            return (
                "The poster restricted who can view this content (age or "
                "region limits) and the bot's account does not qualify. "
                "Editing the account's birth date to match is not worth it - "
                "it risks the account being disabled. "
                f"Details: {detail}"
            )
        # Every method shares Instagram's CDN, so throttling looks like a
        # total failure. Say so rather than blaming the post.
        transient = ("429", "too many requests", "timed out", "timeout",
                     "500 internal server error", "502", "503", "connection")
        if any(w in detail.lower() for w in transient):
            return (
                "Instagram's CDN failed on every method (throttling, timeout "
                "or a server error on their side). Worth retrying in a few "
                f"minutes. Details: {detail}"
            )
        if not self.logged_in:
            return (
                "Instagram download failed and the bot is not logged in. The "
                "logged-out fallbacks handle most public posts, so this is "
                "likely a restricted or removed post. "
                f"Details: {detail}"
            )
        return f"All Instagram download methods failed. Details: {detail}"

    def _download_instagrapi(self, shortcode):
        media_pk = self.client.media_pk_from_code(shortcode)
        result = self.client.private_request(f"media/{media_pk}/info/")

        if not result or not result.get("items"):
            raise RuntimeError("media info response contained no items")

        item = result["items"][0]
        downloaded = 0

        # Handle video (reel or video post)
        if "video_versions" in item and len(item["video_versions"]) > 0:
            video_url = item["video_versions"][0]["url"]
            self._download_file(video_url, f"{shortcode}.mp4")
            downloaded += 1

        # Handle image
        elif "image_versions2" in item:
            candidates = item["image_versions2"].get("candidates", [])
            if candidates:
                image_url = candidates[0]["url"]
                self._download_file(image_url, f"{shortcode}.jpg")
                downloaded += 1

        # Handle carousel (multiple images/videos)
        if "carousel_media" in item:
            for idx, media in enumerate(item["carousel_media"]):
                if "video_versions" in media:
                    url = media["video_versions"][0]["url"]
                    self._download_file(url, f"{shortcode}_{idx + 1}.mp4")
                    downloaded += 1
                elif "image_versions2" in media:
                    url = media["image_versions2"]["candidates"][0]["url"]
                    self._download_file(url, f"{shortcode}_{idx + 1}.jpg")
                    downloaded += 1

        if not downloaded:
            raise RuntimeError("response contained no downloadable media")

    def _download_ytdlp(self, shortcode):
        """Download via yt-dlp, using an exported cookies file when present."""
        ydl_opts = {
            "outtmpl": f"{shortcode}_%(playlist_index|1)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "noplaylist": False,
        }
        if os.path.isfile(self.COOKIES_FILE):
            ydl_opts["cookiefile"] = self.COOKIES_FILE

        # /p/ resolves for reels and posts alike; /reel/ 404s on image posts.
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.instagram.com/p/{shortcode}/"])

    def _download_snapsave(self, shortcode):
        snapsave_utils.download(shortcode)

    def _download_instaloader(self, shortcode):
        self.loader.filename_pattern = "{shortcode}"
        try:
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
        except TypeError as e:
            # instaloader <4.15.3 indexed a null media node without checking,
            # turning a restricted post into a bare TypeError. Kept as a guard
            # in case a future response shape regresses the same way.
            raise RuntimeError("post metadata unavailable (restricted or removed)") from e
        self.loader.download_post(post, target=shortcode)

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
