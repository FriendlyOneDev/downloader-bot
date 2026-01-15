import requests
from parsel import Selector
import os

# Huge thanks to the financiallyruined for his TikTok-Multi-Downloader project
# Majority of this code is from there
# https://github.com/financiallyruined/TikTok-Multi-Downloader


def validate_response(response):
    """Validate that response contains actual media, not an error message."""
    content_type = response.headers.get("Content-Type", "")
    content_length = response.headers.get("Content-Length", "0")

    if "text/" in content_type or "application/json" in content_type:
        raise ValueError(f"Invalid response: got {content_type} instead of media")

    if int(content_length) < 1000 and int(content_length) > 0:
        raise ValueError(f"Response too small ({content_length} bytes), likely an error")

    return True


def downloader(file_name, response, extension, validate=True):
    file_name = f"{file_name}"
    file_path = os.path.join(".", f"{file_name}.{extension}")

    if validate:
        validate_response(response)

    with open(file_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            file.write(chunk)

    if validate and os.path.getsize(file_path) < 1000:
        os.remove(file_path)
        raise ValueError(f"Downloaded file too small, likely an error response")


def download_v1(link, file_name, content_type):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.4",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://tmate.cc",
        "Connection": "keep-alive",
        "Referer": "https://tmate.cc/",
        "Sec-Fetch-Site": "same-origin",
    }

    with requests.Session() as s:
        try:
            response = s.get("https://tmate.cc/", headers=headers)

            selector = Selector(response.text)
            token = selector.css('input[name="token"]::attr(value)').get()
            data = {"url": link, "token": token}

            response = s.post(
                "https://tmate.cc/action", headers=headers, data=data
            ).json()["data"]

            selector = Selector(text=response)

            if content_type == "video":
                download_links = selector.css(
                    ".downtmate-right.is-desktop-only.right a::attr(href)"
                ).getall()

                print(f"Found {len(download_links)} download link(s):")
                for i, link in enumerate(download_links):
                    print(f"[{i}] {link}")

                for link in download_links:
                    print(f"Trying download link: {link}")
                    response = s.get(link, stream=True, headers=headers)

                    # Skip if it's not a real video
                    content_type = response.headers.get("Content-Type", "")
                    if "text/html" in content_type:
                        print("⚠️ Skipping link: got HTML instead of video.")
                        continue

                    # Valid video file, proceed to save
                    downloader(file_name, response, extension="mp4")
                    print("✅ Successfully downloaded video.")
                    break
                else:
                    raise Exception('No valid video links found')
            else:
                download_links = selector.css(".card-img-top::attr(src)").getall()
                for index, download_link in enumerate(download_links):
                    response = s.get(download_link, stream=True, headers=headers)

                    downloader(f"{file_name}_{index}", response, extension="jpeg")

        except Exception as e:
            print(f"\033[91merror\033[0m: {link} - {str(e)}")
            with open("errors.txt", "a") as error_file:
                error_file.write(link + "\n")


def download_v2(link, file_name, content_type):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Sec-Fetch-Site": "same-origin",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://musicaldown.com",
        "Connection": "keep-alive",
        "Referer": "https://musicaldown.com/en?ref=more",
    }

    with requests.Session() as s:
        try:
            # Get initial page
            r = s.get("https://musicaldown.com/en", headers=headers)
            if r.status_code != 200:
                raise Exception(f"Failed to load page, status code: {r.status_code}")

            selector = Selector(text=r.text)

            # Extract tokens with better error handling
            token_a = selector.xpath('//*[@id="link_url"]/@name').get()
            token_b = selector.xpath(
                '//*[@id="submit-form"]/div/div[1]/input[2]/@name'
            ).get()
            token_b_value = selector.xpath(
                '//*[@id="submit-form"]/div/div[1]/input[2]/@value'
            ).get()

            # Check if required tokens were found
            if not token_a:
                raise Exception("Could not find token_a (link_url name attribute)")
            if not token_b:
                raise Exception("Could not find token_b (second input name attribute)")
            if not token_b_value:
                raise Exception(
                    "Could not find token_b_value (second input value attribute)"
                )

            print(f"Found tokens - token_a: {token_a}, token_b: {token_b}")

            # Prepare data
            data = {
                token_a: link,
                token_b: token_b_value,
                "verify": "1",
            }

            # Submit form
            response = s.post(
                "https://musicaldown.com/download", headers=headers, data=data
            )
            if response.status_code != 200:
                raise Exception(
                    f"Failed to submit form, status code: {response.status_code}"
                )

            selector = Selector(text=response.text)

            if content_type == "video":
                # Try multiple possible selectors for video download
                video_selectors = [
                    "/html/body/div[2]/div/div[2]/div[2]/a[3]/@href",
                    "//a[contains(@class, 'download') and contains(text(), 'Download')]/@href",
                    "//a[contains(@href, '.mp4')]/@href",
                    "//div[contains(@class, 'download')]//a/@href",
                ]

                download_link = None
                for xpath in video_selectors:
                    download_link = selector.xpath(xpath).get()
                    if download_link:
                        print(f"Found video download link using selector: {xpath}")
                        break

                if not download_link:
                    raise Exception("Could not find video download link")

                # Download video
                response = s.get(download_link, stream=True, headers=headers)
                if response.status_code != 200:
                    raise Exception(
                        f"Failed to download video, status code: {response.status_code}"
                    )

                downloader(file_name, response, extension="mp4")

            else:  # Images
                # Try multiple selectors for images
                image_selectors = [
                    '//div[@class="card-image"]/img/@src',
                    '//img[contains(@src, "http")]/@src',
                    '//div[contains(@class, "image")]//img/@src',
                ]

                download_links = []
                for xpath in image_selectors:
                    download_links = selector.xpath(xpath).getall()
                    if download_links:
                        print(
                            f"Found {len(download_links)} image links using selector: {xpath}"
                        )
                        break

                if not download_links:
                    raise Exception("Could not find image download links")

                # Download images
                for index, download_link in enumerate(download_links):
                    try:
                        # Convert relative URL to absolute URL
                        if download_link.startswith("/"):
                            download_link = "https://musicaldown.com" + download_link
                        elif not download_link.startswith("http"):
                            download_link = "https://musicaldown.com/" + download_link

                        response = s.get(download_link, stream=True, headers=headers)
                        if response.status_code == 200:
                            downloader(
                                f"{file_name}_{index}", response, extension="jpeg"
                            )
                        else:
                            print(
                                f"Failed to download image {index}, status code: {response.status_code}"
                            )
                    except Exception as img_error:
                        print(f"Error downloading image {index}: {img_error}")

        except Exception as e:
            print(f"\033[91merror\033[0m: {link} - {str(e)}")
            with open("errors.txt", "a") as error_file:
                error_file.write(f"{link} - {str(e)}\n")
            raise Exception


def download_v3(link, file_name, content_type):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "HX-Request": "true",
        "HX-Trigger": "search-btn",
        "HX-Target": "tiktok-parse-result",
        "HX-Current-URL": "https://tiktokio.com/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://tiktokio.com",
        "Connection": "keep-alive",
        "Referer": "https://tiktokio.com/",
    }

    with requests.Session() as s:
        try:
            r = s.get("https://tiktokio.com/", headers=headers)

            selector = Selector(text=r.text)

            prefix = selector.css('input[name="prefix"]::attr(value)').get()

            data = {
                "prefix": prefix,
                "vid": link,
            }

            response = requests.post(
                "https://tiktokio.com/api/v1/tk-htmx", headers=headers, data=data
            )

            selector = Selector(text=response.text)

            if content_type == "video":
                download_link_index = 2
                download_link = selector.css("div.tk-down-link a::attr(href)").getall()[
                    download_link_index
                ]

                response = s.get(download_link, stream=True, headers=headers)

                downloader(file_name, response, extension="mp4")
            else:
                download_links = selector.xpath(
                    '//div[@class="media-box"]/img/@src'
                ).getall()

                for index, download_link in enumerate(download_links):
                    response = s.get(download_link, stream=True, headers=headers)
                    downloader(f"{file_name}_{index}", response, extension="jpeg")

        except Exception as e:
            print(f"\033[91merror\033[0m: {link} - {str(e)}")
            with open("errors.txt", "a") as error_file:
                error_file.write(link + "\n")

            raise Exception


def fallback_download(link, file_name, content_type, max_retries=2):
    methods = [download_v1, download_v2, download_v3]

    for attempt in range(max_retries):
        if attempt > 0:
            print(f"Retry attempt {attempt}/{max_retries - 1}...")

        for func in methods:
            try:
                func(link, file_name, content_type)
                return
            except Exception as e:
                print(f"Failed with {func.__name__}: {str(e)}")

    raise Exception(f"All download methods failed after {max_retries} attempts")


if __name__ == "__main__":
    img_link1 = "https://vm.tiktok.com/ZMSWakLUd/"
    img_link2 = "https://vm.tiktok.com/ZMSWabGYL/"
    img_link3 = "https://vm.tiktok.com/ZMSWashGU/"

    vid_link1 = "https://vm.tiktok.com/ZMDks2TWD/"
    vid_link2 = "https://vm.tiktok.com/ZMSnxfmEC/"
    vid_link3 = "https://vm.tiktok.com/ZMSnx9kG1/"

    print("Downloading using tmate.cc (v1)...")
    download_v1(img_link1, "test_image_1", "photo")
    download_v1(vid_link1, "test_video_1", "video")

    print("Downloading using musicaldown.com (v2)...")
    download_v2(img_link2, "test_image_2", "photo")
    download_v2(vid_link2, "test_video_2", "video")

    print("Downloading using tiktokio.com (v3)...")
    download_v3(img_link3, "test_image_3", "photo")
    download_v3(vid_link3, "test_video_3", "video")
