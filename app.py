import os
import atexit
from pathlib import Path

from flask import Flask, render_template,  request, url_for, g, session
from playwright.sync_api import sync_playwright

from config import Config
from database import db

from logger import logger
from sender import open_whatsapp, send_message
import utils


app = Flask(__name__)
app.config.from_object(Config)


os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.before_request
def before_request():
    utils.init_session()
    logger.debug(f"Обработка запроса: {request.method} {request.path}")


@atexit.register
def on_exit():
    logger.info("Завершение работы приложения")


@app.route("/reset_statuses", methods=["GET"])
def reset_statuses():
    logger.info("Сброс статусов пользователей")
    db.reset_sent_statuses(session["selected_category"])
    g.data = db.get_all_users()
    session["statuses"] = utils.counter_statuses(g.data)

    return utils.go_home_page("Статусы сброшены")


@app.route('/', methods=['GET', 'POST'])
def index():
    logger.debug("Отрисовка главной страницы")
    message = request.args.get("message")
    if message:
        logger.debug(f"[UI MESSAGE] {message}")

    categories = db.get_phones_categories()
    selected_category = session.get('selected_category')
    current_image_url = session.get('current_image_url')

    return render_template(
        'index.html',
        categories=categories,
        message=message,
        selected_category=selected_category,
        current_image_url=current_image_url,
        image_directory_path=session["image_directory_path"],
        length=session["length"],
        sent_message=session.get("text_message"),
        numbers=session["list_numbers"],
        **utils.counter_statuses(g.data, selected_category)
    )


@app.route("/start")
def start():
    if all(contact.status == "sent" for contact in g.filtered_contacts):
        logger.info(
            "Нет ожидающих контактов для отправки сообщений в категории")
        return utils.go_home_page("Нет ожидающих контактов для отправки сообщений")

    with sync_playwright() as playwright:
        page = open_whatsapp(playwright)
        try:
            picture_path = Path(app.config["UPLOAD_FOLDER"]) / "picture.jpg"
            if os.path.isfile(picture_path):
                picture_path = str(picture_path)
            else:
                picture_path = None

            for contact in g.filtered_contacts:
                logger.info(f"Отправка сообщения контакту: {contact.phone}")
                if contact.status == "pending":
                    send_message(
                        contact,
                        picture_path,
                        session["text_message"],
                        page,
                    )

            g.data = db.get_all_users()
            if all(contact.status == "sent" for contact in g.data):
                return utils.go_home_page("Все сообщения отправлены")

            return utils.go_home_page("Messages sent", **session["statuses"])

        except Exception as e:
            logger.exception(f"Ошибка загрузки чатов: {e}")
            qr = "canvas[aria-label*='Scan this QR code']"
            try:
                page.wait_for_selector(qr, timeout=15000)
            except:
                pass

    return utils.go_home_page("Unknown error")


@app.route("/upload", methods=["POST"])
def upload():
    upload_file = request.files.get("file")
    if not upload_file:
        logger.warning("Файл не был передан пользователем")
        return utils.go_home_page("Файл не выбран")

    logger.info(f"Загрузка файла: {upload_file.filename}")
    status = utils.file_processing(upload_file)

    return utils.go_home_page(status)


@app.route("/text", methods=["POST"])
def text():
    logger.info("Пользователь задал текст сообщения")
    session["text_message"] = request.form.get("text") or ""

    uploaded_file = request.files.get("file")
    if uploaded_file and uploaded_file.filename.endswith('.txt'):
        file_content = uploaded_file.read().decode('utf-8')
        session["text_message"] = file_content

    return utils.go_home_page("Текст сообщения сохранен")


@app.route("/set_category", methods=["POST"])
def set_category():
    selected = request.form.get("category")
    logger.info(f"Выбрана категория: {selected}")
    if selected:
        session["selected_category"] = selected
    return utils.go_home_page("Категория изменена")


@app.route('/change_status', methods=['POST'])
def change_status_route():
    phone = request.form.get('phone')
    status = request.form.get('status')
    logger.info(f"Статус изменён: {phone} → {status}")
    utils.change_status(phone, status)
    return utils.go_home_page(f"Статус {phone} изменен.")


@app.route('/delete_number', methods=['POST'])
def delete_number_route():
    phone = request.form.get('phone')
    logger.info(f"Удалён номер: {phone}")
    utils.delete_number(phone)
    return utils.go_home_page(f"{phone} удален.")


@app.route("/add_number", methods=["POST"])
def add_number():
    phone = utils.process_phone_number(request.form.get("phone"))
    logger.info(f"Добавлен номер: {phone}")
    if not phone.isdigit() or len(phone) != 10:
        logger.info("Неверный формат номера")
        return utils.go_home_page(f"Введите 10 цифр после +7 (например, 7011234567)")
    if session["selected_category"] is None:
        logger.debug("Категория не выбрана")
        session["selected_category"] = "Без категории"
    utils.add_number_to_db(phone, session["selected_category"])
    return utils.go_home_page(f"{phone} добавлен.")


if __name__ == "__main__":
    logger.info("Запуск Flask-приложения")
    app.run(debug=True)
