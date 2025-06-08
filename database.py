from tinydb import TinyDB, Query
from models import Contact, Image
import json
from logger import logger


class Database:
    def __init__(self, path="database.json"):
        self.db = TinyDB(path)
        self.contacts = self.db.table('contacts')
        self.images = self.db.table('images')
        self.Contacts = Query()
        self.Images = Query()

    # ===== Contact =====

    def add_user(self, user):
        try:
            if not self.contacts.contains(self.Contacts.phone == user.phone):
                self.contacts.insert(user.to_dict())
                logger.info(f"Добавлен контакт: {user.phone}")
                return True
        except Exception as e:
            logger.exception((f"Ошибка при добавлении пользователя: {e}"))
        return False

    def get_all_users(self):
        try:
            return [Contact.from_dict(contact) for contact in self.contacts.all()]
        except json.JSONDecodeError:
            return []

    def delete_user(self, phone):
        self.contacts.remove(self.Contacts.phone == phone)

    def reset_sent_statuses(self, category):
        self.contacts.update(
            {'status': 'pending'},
            self.Contacts.status == 'sent' and self.Contacts.category == category
        )

    def update_status(self, phone, new_status):
        self.contacts.update(
            {'status': new_status},
            self.Contacts.phone == phone
        )

    def update_name(self, phone, name):
        self.contacts.update({'name': name}, self.Contacts.phone == phone)

    # ===== Images =====

    def add_image(self, image):
        try:
            if not self.images.contains(self.Images.url == image.url):
                self.images.insert(image.to_dict())
                logger.info(f"Добавлено изображение: {image.url}")
                return True
        except Exception as e:
            logger.exception((f"Ошибка при добавлении изображения: {e}"))
        return False

    def get_phones_categories(self):
        return list(set(contact.category for contact in self.get_all_users()))

    def get_phones_by_category(self, category):
        return [contact for contact in self.get_all_users() if contact.category == category]


db = Database()
