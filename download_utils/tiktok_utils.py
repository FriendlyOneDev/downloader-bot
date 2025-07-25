import requests
from parsel import Selector
import os

# Huge thanks to the financiallyruined for his TikTok-Multi-Downloader project
# Majority of this code is from there
# https://github.com/financiallyruined/TikTok-Multi-Downloader


def downloader(file_name, response, extension):
    file_name = f"{file_name}"
    file_path = os.path.join(".", f"{file_name}.{extension}")

    with open(file_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            file.write(chunk)


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
                    print("❌ No valid video links found.")
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
            r = s.get("https://musicaldown.com/en", headers=headers)

            selector = Selector(text=r.text)

            token_a = selector.xpath('//*[@id="link_url"]/@name').get()
            token_b = selector.xpath(
                '//*[@id="submit-form"]/div/div[1]/input[2]/@name'
            ).get()
            token_b_value = selector.xpath(
                '//*[@id="submit-form"]/div/div[1]/input[2]/@value'
            ).get()

            data = {
                token_a: link,
                token_b: token_b_value,
                "verify": "1",
            }

            response = s.post(
                "https://musicaldown.com/download", headers=headers, data=data
            )

            selector = Selector(text=response.text)

            if content_type == "video":
                watermark = selector.xpath(
                    "/html/body/div[2]/div/div[2]/div[2]/a[3]/@href"
                ).get()

                download_link = watermark

                response = s.get(download_link, stream=True, headers=headers)

                downloader(file_name, response, extension="mp4")
            else:
                download_links = selector.xpath(
                    '//div[@class="card-image"]/img/@src'
                ).getall()

                for index, download_link in enumerate(download_links):
                    response = s.get(download_link, stream=True, headers=headers)
                    downloader(f"{file_name}_{index}", response, extension="jpeg")

        except Exception as e:
            print(f"\033[91merror\033[0m: {link} - {str(e)}")
            with open("errors.txt", "a") as error_file:
                error_file.write(link + "\n")


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


def fallback_download(link, file_name, content_type):
    for func in [download_v1, download_v2, download_v3]:
        try:
            func(link, file_name, content_type)
            return
        except Exception as e:
            print(f"Failed with {func.__name__}: {str(e)}")


if __name__ == "__main__":
    img_link1 = "https://vm.tiktok.com/ZMSWakLUd/"
    img_link2 = "https://vm.tiktok.com/ZMSWabGYL/"
    img_link3 = "https://vm.tiktok.com/ZMSWashGU/"

    vid_link1 = "https://vm.tiktok.com/ZMSnxPae1/"
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
