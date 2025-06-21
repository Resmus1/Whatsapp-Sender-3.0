from playwright.sync_api import Playwright, TimeoutError
import os
from logger import logger


def open_whatsapp_profile(playwright: Playwright, profile_name):
    logger.debug("Открытие браузера")
    profile_path = os.path.join("browser/profiles", profile_name)
    os.makedirs(profile_path, exist_ok=True)

    browser = playwright.chromium.launch_persistent_context(
        user_data_dir=f"browser/profiles/{profile_name}",
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
    logger.debug("Открываю WhatsApp Web...")
    page.goto("https://web.whatsapp.com/")

    while True:
        try:
            logger.debug("Пробуем найти элемент, означающий вход...")
            page.wait_for_selector("div.x78zum5.xdt5ytf.x5yr21d", timeout=60000)
            logger.info("Авторизация успешна!")
            return page
        except TimeoutError:
            logger.debug("Элемент не появился. Повторяем...")


def close_browser(playwright):
    playwright.stop()