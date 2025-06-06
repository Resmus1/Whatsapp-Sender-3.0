import os
import random
import requests
from flask import url_for, redirect, current_app, session, g
from database import db
from models import Contact, Image
from collections import Counter


def file_processing(file):
    ext = file.filename.rsplit('.')[-1].lower()

    if ext == "txt":
        file_content = file.read().decode("utf-8")
        file_name = file.filename.rsplit('.')[0]
        file_content = [row.strip()
                        for row in file_content.split('\n') if row.strip()]
        status = save_numbers(file_content, file_name)

    elif ext == "jpg":
        status = save_image_to_disk(file.read())
    else:
        return "Неподдерживаемый формат файла."
    return status


def save_image_to_disk(image_bytes):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_filename = "picture.jpg"
    image_path = os.path.join(upload_folder, image_filename)

    with open(image_path, "wb") as f:
        f.write(image_bytes)

    session["image_path"] = url_for(
        "static", filename=f"uploads/{image_filename}")
    return "Image uploaded."

def save_numbers(numbers, category):
    added, skipped = 0, 0

    for phone_number in numbers:
        contact = Contact(phone=phone_number, category=category)
        if db.add_user(contact):
            added += 1
        else:
            skipped += 1

    return f"Загружено {added} новых контактов. {skipped} контактов уже существуют."


def read_image():
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_path = os.path.join(upload_folder, "picture.jpg")

    if os.path.exists(image_path):
        return url_for("static", filename="uploads/picture.jpg")
    return None


def process_text_message(text_message, page):
    text_field = page.get_by_role("textbox", name="Добавьте подпись")
    text_field.click()
    text_field.fill(text_message)

def get_display_numbers(users, selected_category):
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


def update_image_length():
    selected_category = session.get("selected_category")
    if selected_category:
        length = len(db.get_phones_by_category(selected_category))
    else:
        length = 0
    return length


def init_session():
    session["image_directory_path"] = read_image()
    session["text_message"] = session.get("text_message", "")
    session["selected_category"] = session.get("selected_category", None)
    g.data = db.get_all_users() or []
    session["categories"] = db.get_phones_categories()
    session["length"] = update_image_length()


def change_status(phone, status):
    db.update_status(phone, status)
    session["statuses"] = counter_statuses(g.data)


def delete_number(phone):
    db.delete_user(phone)
    session["statuses"] = counter_statuses(g.data)


def add_number_to_db(phone):
    contact = Contact(phone=phone)
    db.add_user(contact)
    session["statuses"] = counter_statuses(g.data)


def process_phone_number(phone):
    cleaned = phone.replace(" ", "").replace(
        "-", "").replace("(", "").replace(")", "").replace(".", "").strip()
    if cleaned.startswith("+7"):
        cleaned = cleaned[2:]
    elif cleaned.startswith("8"):
        cleaned = cleaned[1:]
    return cleaned


def go_home_page(message):
    return redirect(url_for('index', message=message))
