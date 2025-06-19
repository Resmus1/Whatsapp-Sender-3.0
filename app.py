import os
import atexit
import sched
import time
import re

from flask import Flask, render_template,  request, g, session
from services import sender_service, file_service

from config import Config
from database import db

from logger import logger
from utils import init_session, counter_statuses, go_home_page, change_status, delete_number, process_phone_number, add_number_to_db


app = Flask(__name__)
app.config.from_object(Config)

scheduler = sched.scheduler(time.time, time.sleep)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.before_request
def before_request():
    init_session()
    logger.debug(f"Обработка запроса: {request.method} {request.path}")


@atexit.register
def on_exit():
    logger.info("Завершение работы приложения")


@app.route("/reset_statuses", methods=["GET"])
def reset_statuses():
    logger.info("Сброс статусов пользователей")
    db.reset_sent_statuses(session["selected_category"])
    g.data = db.get_all_users()
    session["statuses"] = counter_statuses(g.data)

    return go_home_page("Статусы сброшены")


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
        length=g.length,
        length_messages=g.length_messages,
        position_message=session.get("position_message", 0),
        sent_message=session.get("text_message"),
        numbers=g.processed_numbers,
        **counter_statuses(g.data, selected_category)
    )


@app.route("/start")
def start():
    message = sender_service.send_pending_contacts()
    return go_home_page(message)


@app.route("/upload_image", methods=["POST"])
def upload_image():
    upload_file = request.files.get("file")
    status = file_service.save_image_file(upload_file)
    logger.info(f"Файл сохранён: {upload_file}")

    return go_home_page(status)


@app.route("/upload_contacts", methods=["POST"])
def upload_contacts():
    uploaded_file = request.files.get("file")
    status = file_service.contacts_file_processing(uploaded_file)
    logger.info(f"Файл сохранён: {uploaded_file}")

    return go_home_page(status)


@app.route("/text", methods=["POST"])
def handle_text():
    uploaded_file = request.files.get("file")
    if uploaded_file:
        status = file_service.handle_text_file(uploaded_file)

    else:
        session["text_message"] = request.form.get("text") or ""
        action = request.form.get("action")
        status = file_service.handle_text_action(action)

    return go_home_page(status)


@app.route("/set_category", methods=["POST"])
def set_category():
    selected = request.form.get("category")
    logger.info(f"Выбрана категория: {selected}")
    if selected:
        session["selected_category"] = selected
    return go_home_page("Категория изменена")


@app.route("/delete_category", methods=["POST"])
def delete_category():
    db.delete_contacts_by_category(session["selected_category"])
    logger.info(f"Категория удалена: {session['selected_category']}")
    return go_home_page("Категория удалена")


@app.route('/change_status', methods=['POST'])
def change_status_route():
    phone = request.form.get('phone')
    status = request.form.get('status')
    logger.info(f"Статус изменён: {phone} → {status}")
    change_status(phone, status)
    return go_home_page(f"Статус {phone} изменен.")


@app.route('/delete_number', methods=['POST'])
def delete_number_route():
    phone = request.form.get('phone')
    logger.info(f"Удалён номер: {phone}")
    delete_number(phone)
    return go_home_page(f"{phone} удален.")


@app.route("/add_number", methods=["POST"])
def add_number():
    phone = process_phone_number(request.form.get("phone"))
    logger.info(f"Добавлен номер: {phone}")
    if not re.fullmatch(r"\d{10}", phone):
        logger.info("Неверный формат номера")
        return go_home_page(f"Введите 10 цифр после +7 (например, 7011234567)")
    if session["selected_category"] is None:
        logger.debug("Категория не выбрана")
        session["selected_category"] = "Без категории"
    add_number_to_db(phone, session["selected_category"])
    return go_home_page(f"{phone} добавлен.")


@app.route("/create_profile", methods=["POST"])
def create_profile():
    name = request.form.get("profile_name")
    print(name)
    db.add_profile(name)
    logger.info(f"Создан профиль: {name}")
    return go_home_page("Профиль создан.")


if __name__ == "__main__":
    logger.info("Запуск Flask-приложения")
    app.run(debug=True)
