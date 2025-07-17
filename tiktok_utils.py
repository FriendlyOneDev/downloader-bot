from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager


class TikTokScraper:
    def __init__(self, headless=True):
        # Setup Chrome options
        self.options = webdriver.ChromeOptions()
        if headless:
            self.options.add_argument("--headless")

        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--disable-popup-blocking")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")

        self.options.add_argument(
            f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
        )

        self.service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=self.service, options=self.options)

        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        stealth(
            self.driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

    def get_screenshot(self, url):
        self.driver.get(url)
        return self.driver.get_screenshot_as_png()

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    scraper = TikTokScraper(headless=True)
    png_data = scraper.get_screenshot("https://www.tiktok.com")

    with open("screenshot.png", "wb") as f:
        f.write(png_data)

    scraper.close()
