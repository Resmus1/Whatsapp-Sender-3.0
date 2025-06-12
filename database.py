from tinydb import TinyDB, Query
from models import Contact, Message
import json
from logger import logger


class Database:
    def __init__(self, path="database.json"):
        self.db = TinyDB(path)
        self.contacts = self.db.table('contacts')
        self.messages = self.db.table('messages')
        self.Contacts = Query()
        self.Messages = Query()

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

    def get_phones_categories(self):
        return list(set(contact.category for contact in self.get_all_users()))

    def get_phones_by_category(self, category):
        return [contact for contact in self.get_all_users() if contact.category == category]

    # ===== Message =====

    def add_message(self, message):
        try:
            if not self.messages.contains(self.Messages.text == message.text):
                self.messages.insert(message.to_dict())
                logger.debug(f"Добавлено сообщение: {message.text}")
                return True
        except Exception as e:
            logger.exception((f"Ошибка при добавлении сообщения: {e}"))
        return False

    def count_messages(self):
        count = sum(
            1 for message in self.messages.all()
            if Message.from_dict(message).category == "info"
        )
        return count

    def get_messages(self, category):
        try:
            messages = list(
                Message.from_dict(message)
                for message in self.messages.all()
                if message['category'] == category
            )

            return messages
        except json.JSONDecodeError:
            return []


    def delete_message(self, text_message):
        self.messages.remove(self.Messages.text == text_message)


db = Database()
