from flask import Flask, g, session
from logger import logger
import os
from pathlib import Path
from config import Config
from utils import split_contacts, processing_cycle
from playwright.sync_api import sync_playwright
from database import db
from browser import open_whatsapp

app = Flask(__name__)
app.config.from_object(Config)


def send_pending_contacts():
    logger.debug("Получение контактов для обработки")
    pending_contacts = [
        c for c in g.filtered_contacts if c.status == "pending"]
    lists_pending_contacts = split_contacts(pending_contacts)
    logger.info(f"Количество ожидающих контактов: {len(pending_contacts)}")
    logger.debug(
        f"Количество списков ожидающих контактов: {len(lists_pending_contacts)}")

    if not pending_contacts:
        logger.info("Нет ожидающих контактов для отправки сообщений")
        return "Нет ожидающих контактов для отправки сообщений"

    with sync_playwright() as playwright:
        page = open_whatsapp(playwright)
        try:
            picture_path = Path(
                app.config["UPLOAD_FOLDER"]) / "PICTURE_FILENAME"
            if os.path.isfile(picture_path):
                picture_path = str(picture_path)
            else:
                picture_path = None

            for i, list_pending_contacts in enumerate(lists_pending_contacts, 1):
                logger.info(
                    f"[{i}/{len(lists_pending_contacts)}] Запуск цикла обработки списка контактов")
                processing_cycle(
                    page, picture_path, list_pending_contacts)

            g.data = db.get_all_users()
            if all(contact.status == "sent" for contact in g.data):
                return "Все сообщения отправлены"

            return "Messages sent", session["statuses"]

        except Exception as e:
            logger.exception(f"Ошибка загрузки чатов: {e}")
            qr = "canvas[aria-label*='Scan this QR code']"
            try:
                page.wait_for_selector(qr, timeout=15000)
            except:
                pass

    return " Неизвестная ошибка"
