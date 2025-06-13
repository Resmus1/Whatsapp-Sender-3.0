import os
import atexit
import sched
import time
import re

from flask import Flask, render_template,  request, g, session
from services import sender_service

from config import Config
from database import db

from logger import logger
import utils


app = Flask(__name__)
app.config.from_object(Config)

scheduler = sched.scheduler(time.time, time.sleep)

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
        length_messages=session["length_messages"],
        position_message=session.get("position_message", 0),
        sent_message=session.get("text_message"),
        numbers=session["list_numbers"],
        **utils.counter_statuses(g.data, selected_category)
    )


@app.route("/start")
def start():
    message = sender_service.send_pending_contacts()
    return utils.go_home_page(message)


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
def handle_text():
    uploaded_file = request.files.get("file")
    if uploaded_file and uploaded_file.filename.endswith('.txt'):
        file_content = uploaded_file.read().decode('utf-8')
        session["text_message"] = file_content
        utils.add_message_to_db(session["text_message"])
        return utils.go_home_page("Текст из файла загружен")

    session["text_message"] = request.form.get("text") or ""
    action = request.form.get("action")

    if action == "next":
        if session["position_message"] < session["length_messages"] - 1:
            session["position_message"] += 1
            session["text_message"] = utils.get_index_message(
                session["position_message"])

    elif action == "prev":
        if session["position_message"] > 0:
            session["position_message"] -= 1
            session["text_message"] = utils.get_index_message(
                session["position_message"])

    elif action == "save":
        utils.add_message_to_db(session["text_message"])
        return utils.go_home_page("Текст сообщения сохранен")
    elif action == "delete":
        utils.delete_message_in_db(session["text_message"])
        return utils.go_home_page("Текст сообщения удален")

    return utils.go_home_page("Нет действия или неизвестная команда")


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
    if not re.fullmatch(r"\d{10}", phone):
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
