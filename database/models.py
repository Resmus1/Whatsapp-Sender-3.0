class Contact:
    def __init__(self, phone, name=None, category=None, status='pending'):
        self.name = name
        self.phone = phone
        self.category = category
        self.status = status

    def to_dict(self):
        return {
            'name': self.name,
            'phone': self.phone,
            'category': self.category,
            'status': self.status
        }

    @staticmethod
    def from_dict(data):
        return Contact(data['phone'], data.get('name'), data.get('category'), data['status'])


class Message:
    def __init__(self, text, category='info'):
        self.text = text
        self.category = category

    def to_dict(self):
        return {
            'text': self.text,
            'category': self.category
        }
    
    @staticmethod
    def from_dict(data):
        return Message(data['text'], data.get('category'))


class Profile:
    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {"name": self.name}
    
    @staticmethod
    def from_dict(data):
        return Profile(data["name"])