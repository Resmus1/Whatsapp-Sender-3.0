from playwright.sync_api import Playwright
from database import db
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
    page.goto("https://web.whatsapp.com/")
    return page


def send_message(contact, picture_path, text_message, page,):
    new_chat(page, contact)
    if contact.name == None:
        try:
            name = page.locator(
                '//*[@id="main"]/header/div[2]/div/div/div/div/span').text_content()
            db.update_name(contact.phone, name)
        except Exception as e:
            print(f"Ошибка при получении имени контакта {contact.phone}: {e}")
            db.update_status(contact.phone, "error")
            return False

    processed_message(page, picture_path, text_message)

    # page.get_by_role("button", name="Отправить").click()
    logger.info("Сообщение отправлено")
    page.wait_for_timeout(1000)
    db.update_status(contact.phone, "sent")


def new_chat(page, contact):
    logger.debug(f"Новый чат с контактом: {contact.phone}")
    new_chat_button = page.wait_for_selector(
        '[data-icon="new-chat-outline"]', timeout=15000)
    new_chat_button.click()
    search_box = page.get_by_role(
        "textbox", name="Поиск по имени или номеру")

    search_box.click()
    search_box.fill(contact.phone)
    page.wait_for_timeout(2000)
    search_box.press("Enter")
    logger.debug(f"Контакт открыт: {contact.phone}")


def processed_message(page, picture_path, text_message):
    logger.debug("Обработка сообщения")
    if picture_path is not None:
        logger.debug("Прикрепление изображения")
        page.get_by_role("button", name="Прикрепить").click()
        page.locator(
            "(//input[@type='file'])[2]").set_input_files(picture_path)
        logger.debug("Добавление подписи")
        text_field = page.get_by_role("textbox", name="Добавьте подпись")
        text_field.click()
        text_field.fill(text_message)
    else:
        logger.debug("Написание текста")
        text_field = page.get_by_role("textbox", name="Введите сообщение")
        text_field.click()
        text_field.type(text_message)


def close_browser(playwright):
    playwright.stop()
