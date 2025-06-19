from playwright.sync_api import Playwright
from logger import logger

def open_whatsapp(playwright: Playwright):
    logger.debug("Открытие браузера")
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir="profile",
        headless=False,
        args=[
            "--disable-application-cache",
            "--disk-cache-size=1",
            "--start-maximized"
        ]
    )
    page = browser.pages[0] if browser.pages else browser.new_page()
    enter_whatsapp(page)
    return page

def enter_whatsapp(page):
    logger.debug("Вход в WhatsApp")
    page.goto("https://web.whatsapp.com/")
    while True:
        try:
            logger.debug("Подтверждение входа")
            page.wait_for_selector("div.x78zum5.xdt5ytf.x5yr21d", timeout=60000)
            return page
        except TimeoutError:
            logger.debug("Подтверждение входа не получено, повторная попытка")


def close_browser(playwright):
    playwright.stop()
