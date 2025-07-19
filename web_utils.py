import instaloader
import re


class LinkHandler:
    def __init__(self):
        self.link_pattern = re.compile(
            r"""
            https?:\/\/
            (?:www\.)?
            (?:
                reddit\.com\/r\/[\w]+\/comments\/[\w]+(?:\/[\w_]+)?\/? |
                redd\.it\/[\w]+ |
                instagram\.com\/(?:reel|p)\/[\w-]+\/?(?:\?[^\s]*)? |
                tiktok\.com\/@[\w.-]+\/(?:video|photo)\/\d+ |
                tiktok\.com\/embed(?:\/v2)?\/\d+ |
                vm\.tiktok\.com\/[\w\/]+
            )
            \/?
            (?:\?[^\s]*)?
            """,
            re.VERBOSE,
        )
        self.shortcode_pattern = re.compile(
            r"""
            (?:https?:\/\/(?:www\.)?)
            (?:
                instagram\.com\/(?:reel|p)\/(?P<instagram_shortcode>[\w-]+) |
                reddit\.com\/r\/[\w]+\/comments\/(?P<reddit_shortcode>[\w]+) |
                vm\.tiktok\.com\/(?P<tiktok_shortcode_short>[^\/\?\s]+) |  
                tiktok\.com\/@[\w.-]+\/video\/(?P<tiktok_shortcode_long>\d+)
            )
            """,
            re.VERBOSE,
        )

    def extract_shortcode(self, url):
        match = self.shortcode_pattern.search(url)
        if not match:
            return None

        return next(
            (group for group in match.groupdict().values() if group is not None), None
        )


def instaloader_init():
    return instaloader.Instaloader(
        download_comments=False,
        download_geotags=False,
        download_pictures=False,
        download_video_thumbnails=False,
        save_metadata=False,
    )
