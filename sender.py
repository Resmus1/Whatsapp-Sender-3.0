from playwright.sync_api import Playwright
from database import db
from logger import logger
import random


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
    page.goto("https://web.whatsapp.com/", timeout=60000)
    return page


def send_message(contact, picture_path, text_message, page,):
    search_box = page.get_by_role(
        "textbox", name="Поиск по имени или номеру")

    new_chat(page, contact, search_box)

    if page.locator("text=Не найдено").first.is_visible():
        logger.error("Контакт не найден")
        page.screenshot(path=f"logs/errors/{contact.phone}.png")
        db.update_status(contact.phone, "error")
        search_box.press("Escape")
        page.wait_for_timeout(1000)
        return

    if contact.name == None:
        check_name(page, contact)

    text_field = page.get_by_role("textbox", name="Введите сообщение")
    send_button = page.get_by_role("button", name="Отправить")

    say_hello(page, contact, text_field, send_button)
    processed_message(page, contact, picture_path, text_field, send_button, text_message)

    # page.get_by_role("button", name="Отправить").click()
    logger.info("Сообщение отправлено")
    page.wait_for_timeout(1000)
    db.update_status(contact.phone, "sent")


def new_chat(page, contact, search_box):
    logger.debug(f"Новый чат с контактом: {contact.phone}")
    new_chat_button = page.wait_for_selector(
        '[data-icon="new-chat-outline"]', timeout=15000)
    new_chat_button.click()

    search_box.click()
    search_box.fill(contact.phone)
    page.wait_for_timeout(2000)
    search_box.press("Enter")


def say_hello(page, contact, text_field, send_button):
    logger.debug("Приветствие")
    hello = random.choice(db.get_messages(category='hello')).text
    try:
        text_field.click()
        text_field.type(hello)
        # send_button.click()
        page.wait_for_timeout(random.randint(3000, 5000))
    except Exception as e:
        logger.error(f"Ошибка при отправке приветствия: {e}")
        page.screenshot(path=f"logs/errors/{contact.phone}.png")


def processed_message(page, contact, picture_path, text_field, send_button, text_message):
    logger.debug("Обработка сообщения")
    if picture_path is not None:
        try:
            logger.debug("Прикрепление изображения")
            page.get_by_role("button", name="Прикрепить").click()
            page.locator(
                "(//input[@type='file'])[2]").set_input_files(picture_path)
            logger.debug("Добавление подписи")
        except Exception as e:
            logger.error(f"Ошибка при отправки изображения: {e}")
            page.screenshot(path=f"logs/errors/{contact.phone}.png")
            db.update_status(contact.phone, "error")
    else:
        logger.debug("Написание текста")
    try:
        text_field.click()
        text_field.type(text_message)
        # send_button.click()
    except Exception as e:
        logger.error(f"Ошибка при отправке приветствия: {e}")
        page.screenshot(path=f"logs/errors/{contact.phone}.png")
        db.update_status(contact.phone, "error")


def check_name(page, contact):
    logger.debug("Получение имени контакта")
    try:
        name = page.locator(
            '//*[@id="main"]/header/div[2]/div/div/div/div/span').text_content()
        db.update_name(contact.phone, name)
    except Exception as e:
        print(f"Ошибка при получении имени контакта {contact.phone}: {e}")
        page.screenshot(path=f"logs/errors/{contact.phone}.png")
        db.update_status(contact.phone, "error")
        return False


def close_browser(playwright):
    playwright.stop()
