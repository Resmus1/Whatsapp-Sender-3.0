import os
import time
import random
from flask import url_for, redirect, current_app, session, g
from database import Contact, db
from collections import Counter
from logger import logger
from sender import send_message


def read_image():
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_path = os.path.join(upload_folder, "picture.jpg")

    if os.path.exists(image_path):
        return url_for("static", filename="uploads/picture.jpg")
    return None


def get_processed_numbers(users, selected_category):
    return [
        {
            "number": getattr(user, "phone"),
            "name": getattr(user, "name"),
            "status": getattr(user, "status"),
        }
        for user in users if user.category == selected_category
    ]


def counter_statuses(contacts, selected_category=None):
    return dict(Counter([contact.status for contact in contacts if contact.category == selected_category]))


def init_session():
    session["image_directory_path"] = read_image()
    session["text_message"] = session.get("text_message", "")
    session["categories"] = db.get_phones_categories()
    session["selected_category"] = session.get("selected_category", None)
    session["position_message"] = session.get("position_message", 0)
    g.data = db.get_all_users() or []

    if session["selected_category"]:
        g.filtered_contacts = [
            c for c in g.data if c.category == session["selected_category"]
        ]
    else:
        g.filtered_contacts = {}

    g.processed_numbers = get_processed_numbers(
        g.data, session["selected_category"])
    g.length = len( g.processed_numbers)
    g.length_messages = db.count_messages()


def change_status(phone, status):
    db.update_status(phone, status)
    session["statuses"] = counter_statuses(g.filtered_contacts)


def delete_number(phone):
    db.delete_user(phone)
    session["statuses"] = counter_statuses(g.filtered_contacts)


def add_number_to_db(phone, category):
    contact = Contact(phone=phone, category=category)
    db.add_user(contact)
    session["statuses"] = counter_statuses(g.filtered_contacts)


def process_phone_number(phone):
    cleaned = phone.replace(" ", "").replace(
        "-", "").replace("(", "").replace(")", "").replace(".", "").strip()
    if cleaned.startswith("+7"):
        cleaned = cleaned[2:]
    elif cleaned.startswith("8"):
        cleaned = cleaned[1:]
    return cleaned


def get_index_message(index_message):
    messages = db.get_messages(category='info')
    if not messages:
        return ""
    return messages[index_message].text


def processing_cycle(page, picture_path, pending_contacts, count):
    logger.debug("Запуск цикла обработки")
    start_time = time.time()
    pauses = random_pauses(3600, count - 1, 120, 300)
    logger.info(f"Генерация {len(pauses)} пауз: {pauses}")

    for i, contact in enumerate(pending_contacts, 1):
        logger.info(f"[{i}/{count}] Обработка контакта: {contact.phone}")
        send_message(
            contact,
            picture_path,
            page,
        )
        if i != count:
            logger.info(f"Осталось отправить {count - i} сообщений")
            pause = pauses[i - 1]
            logger.info(f"Пауза {pause} секунд")
            time.sleep(pause)

    elapsed_time = time.time() - start_time
    logger.debug(f"Обработка завершена за {elapsed_time} секунд")

    remaining = 3600 - elapsed_time
    logger.info(f"Завершение обработки. Осталось {remaining} секунд")
    if remaining > 0:
        logger.info(f"Ждём остаток часа: {int(remaining)} секунд")
        time.sleep(remaining)
        logger.debug("Цикл обработки завершён")


def random_pauses(total, n, min_pause=30, max_pause=300):
    weights = [random.uniform(min_pause, max_pause) for _ in range(n)]
    factor = total / sum(weights)
    return [int(w * factor) for w in weights]


def split_contacts(contacts, min_size=15, max_size=20):
    logger.debug("Разделение контактов на списки")
    chunks = []
    i = 0
    while i < len(contacts):
        remaining = len(contacts) - i
        if remaining <= min_size:
            chunks.append(contacts[i:])
            logger.debug("Осталось мало контактов для разделения")
            break
        chunk_size = random.randint(min_size, max_size)
        chunks.append(contacts[i:i + chunk_size])
        i += chunk_size
    return chunks


def go_home_page(message):
    return redirect(url_for('index', message=message))
