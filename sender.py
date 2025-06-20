from playwright.sync_api import TimeoutError
from database import db
from logger import logger
import random
import time


def send_message(contact, picture_path, page, processing_time):
    search_box = page.get_by_role(
        "textbox", name="Поиск по имени или номеру")

    new_chat(page, contact, search_box)

    if page.locator("text=Не найдено").first.is_visible():
        logger.error("Контакт не найден")
        page.screenshot(path=f"logs/errors/{contact.phone}.png")
        db.update_status(contact.phone, "error")
        return

    if contact.name == None:
        check_name(page, contact)

    text_field = page.get_by_role("textbox", name="Введите сообщение")
    send_button = page.get_by_role("button", name="Отправить")

    processed_messages(
        page, contact, text_field,
        picture_path, send_button, processing_time
    )

    logger.info("Сообщение отправлено")
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
        answer = wait_for_new_message(page, deadline)
        if answer:
            logger.debug(f"Ответ получен отправка следующего сообщения")
            page.wait_for_timeout(random.randint(1000, 3000))
        else:
            logger.debug("Дедлайн истек, отправка следующего сообщения")

    except TimeoutError:
        logger.debug("Ответ не получен, отправка следующего сообщения")

    finally:
        sending_message(page, contact, picture_path, text_field, send_button)
        remaining_time = processing_time - (time.time() - start_time)
        logger.debug(
            f"Оставшееся время обработки: {remaining_time:.2f} секунд")
        if remaining_time > 0:
            time.sleep(remaining_time)


def wait_for_new_message(page, deadline, poll_interval=0.2):
    page.wait_for_timeout(10000)
    logger.debug("Поиск входящих сообщений")
    locator = page.locator(
        "div.message-in.focusable-list-item._amjy._amjz._amjw.x1klvx2g.xahtqtb")

    try:
        start_count = locator.count()
    except Exception as e:
        logger.warning(
            f"Ошибка при подсчете начального количества сообщений: {e}")
        start_count = 0

    logger.debug(f"Начальное количество сообщений: {start_count}")

    if deadline - time.time() < 5:
        logger.debug(
            "До дедлайна осталось меньше 5 секунд — пропускаем ожидание")
        return False

    while time.time() < deadline - 5:
        try:
            current_count = locator.count()
            if current_count > start_count:
                logger.debug(
                    f"Новое сообщение получено: {current_count} (было {start_count})")
                return True
        except Exception as e:
            logger.debug(f"Ошибка при проверке количества сообщений: {e}")
        time.sleep(poll_interval)

    logger.debug(
        f"Сообщения не изменились за отведённое время (осталось: {round(deadline - time.time(), 1)} сек)")


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