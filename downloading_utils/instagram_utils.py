import instaloader


class InstagramHandler:
    def __init__(self):
        self.instaloader = instaloader.Instaloader(
            download_comments=False,
            download_geotags=False,
            download_pictures=False,
            download_video_thumbnails=False,
            save_metadata=False,
            post_metadata_txt_pattern="",
        )

    def download_post(self, shortcode):
        self.instaloader.filename_pattern = "{shortcode}"
        post = instaloader.Post.from_shortcode(self.instaloader.context, shortcode)
        self.instaloader.download_post(post, target=shortcode)


if __name__ == "__main__":
    handler = InstagramHandler()
    # Example usage
    shortcode = "DG_OqyBsqSC"
    handler.download_post(shortcode)
