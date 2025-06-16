from playwright.sync_api import Playwright, TimeoutError 
from database import db
from logger import logger
import random
import time


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


def send_message(contact, picture_path, page, processing_time):
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

    processed_messages(page, contact, text_field, picture_path, send_button, processing_time)

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
        # page.wait_for_selector('span[aria-live="polite"]:has-text("непрочитанное сообщение")', timeout=15000)
        # page.wait_for_timeout(random.randint(3000, 15000))
    except Exception as e:
        logger.error(f"Ошибка при отправке приветствия: {e}")
        page.screenshot(path=f"logs/errors/{contact.phone}.png")


def sending_message(page, contact, picture_path, text_field, send_button):
    logger.debug("Отправка сообщения")
    text_message = random.choice(db.get_messages(category='info')).text
    if picture_path is not None:
        try:
            logger.debug("Прикрепление изображения")
            page.get_by_role("button", name="Прикрепить").click()
            page.locator(
                "(//input[@type='file'])[2]").set_input_files(picture_path)
            logger.debug("Добавление подписи")
            text_field = page.get_by_role("textbox", name="Добавьте подпись")
            text_field.click()
            text_field.type(text_message)
            # send_button.click()
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


def processed_messages(page, contact, text_field, picture_path, send_button, processing_time):
    logger.debug("Обработка сообщений")
    start_time = time.time()
    logger.info(f"Время обработки: {processing_time} секунд")
    deadline = start_time + processing_time

    say_hello(page, contact, text_field, send_button)

    try:
        logger.debug(f"Дедлайн: {deadline}, текущее время: {time.time()}, осталось: {round(deadline - time.time(), 2)} сек")
        wait_for_new_message(page,deadline)

        logger.debug(f"Ответ получен отправка следующего сообщения")
        page.wait_for_timeout(random.randint(1000, 3000))

    except TimeoutError:
        logger.debug("Ответ не получен, отправка следующего сообщения")

    finally:
        sending_message(page, contact, picture_path, text_field, send_button)
        remaining_time = processing_time - (time.time() - start_time)
        logger.debug(f"Оставшееся время обработки: {remaining_time:.2f} секунд")
        if remaining_time > 0:
            time.sleep(remaining_time)


def wait_for_new_message(page, deadline, poll_interval=0.2):
    logger.debug("Подсчет входящих сообщений")
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    page.wait_for_timeout(2000)
    locator = page.locator("div.x3psx0u.xwib8y2.x1c1uobl.xrmvbpv >> .x1n2onr6")

    try:
        start_count = locator.count()
    except Exception as e:
        logger.warning(f"Ошибка при подсчете начального количества сообщений: {e}")
        start_count = 0

    logger.debug(f"Начальное количество сообщений: {start_count}")

    if deadline - time.time() < 5:
        logger.debug("До дедлайна осталось меньше 5 секунд — пропускаем ожидание")
        return start_count

    while time.time() < deadline - 5:
        try:
            current_count = locator.count()
            print(current_count)
            if current_count > start_count:
                logger.debug(f"Новое сообщение получено: {current_count} (было {start_count})")
                return current_count
        except Exception as e:
            logger.debug(f"Ошибка при проверке количества сообщений: {e}")
        time.sleep(poll_interval)

    logger.debug(f"Сообщения не изменились за отведённое время (осталось: {round(deadline - time.time(), 1)} сек)")



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
