import json
from werkzeug.datastructures import FileStorage
from logger import logger
from config import Config
from pathlib import Path
from database import db
from database import Contact, Message
from flask import session, g
from utils import get_index_message


def save_image_file(upload_file: FileStorage) -> str:
    if upload_file and upload_file.filename.endswith(".jpg"):
        upload_path = Path(Config.UPLOAD_FOLDER) / Config.PICTURE_FILENAME
        upload_file.save(upload_path)

    else:
        return "Неподдерживаемый формат файла. Только jpg"

    return "Файл jpg успешно загружен"


def contacts_file_processing(upload_file: FileStorage) -> str:
    if upload_file:
        ext = upload_file.filename.split(".")[-1]
        file_name = upload_file.filename.split(".")[0]
        content = read_uploaded_file(upload_file)

        if ext == "txt":
            lines = [row.strip()
                     for row in content.split('\n') if row.strip()]
            status = save_numbers(lines, file_name)
            return status

        elif ext == "json":
            data = json.loads(content)
            save_numbers_json(data, file_name)
            return None

    return "Неподдерживаемый формат файла. Только txt и csv"


def handle_text_file(upload_file: FileStorage) -> str:
    if upload_file and upload_file.filename.endswith(".txt"):
        read_file_content = read_uploaded_file(upload_file)
        session["text_message"] = read_file_content
        db.add_message(Message(read_file_content))
        logger.info("Текст загружен из файла")
        return "Текст из файла загружен"

    return "Неподдерживаемый формат файла. Только txt"


def handle_text_action(action: str) -> str:
    if action == "next":
        if session["position_message"] < g.length_messages - 1:
            session["position_message"] += 1
            session["text_message"] = get_index_message(
                session["position_message"])

    elif action == "prev":
        if session["position_message"] > 0:
            session["position_message"] -= 1
            session["text_message"] = get_index_message(
                session["position_message"])

    elif action == "save":
        db.add_message(Message(session["text_message"]))
        return "Текст сообщения сохранен"

    elif action == "delete":
        db.delete_message(session["text_message"])
        return "Текст сообщения удален"
    return "Нет действия или неизвестная команда"


def read_uploaded_file(upload_file: FileStorage) -> str:
    return upload_file.read().decode("utf-8")


def save_numbers(numbers: list[str], category: str) -> str:
    added, skipped = 0, 0

    for phone_number in numbers:
        contact = Contact(phone=phone_number, category=category)
        if db.add_user(contact):
            added += 1
        else:
            skipped += 1
    if skipped:
        logger.info(f"{skipped} номеров уже существовали и были пропущены.")

    return f"Загружено {added} новых контактов. {skipped} контактов уже существуют."


def save_numbers_json(data, category: str) -> str:
    added, skipped = 0, 0

    for contact_data in data:
        name = contact_data["name"]
        whatsapp = contact_data["socials"]["WhatsApp"]
        for i, phone_number in enumerate(whatsapp):
            contact = Contact(phone=phone_number, name=name if i ==
                              0 else name + str(i), category=category)
            if db.add_user(contact):
                added += 1
            else:
                skipped += 1
    if skipped:
        logger.info(f"{skipped} номеров уже существовали и были пропущены.")

    return f"Загружено {added} новых контактов. {skipped} контактов уже существуют."
