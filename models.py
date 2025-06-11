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
    def __init__(self, text):
        self.text = text

    def to_dict(self):
        return {
            'text': self.text,
        }
    
    @staticmethod
    def from_dict(data):
        return Message(data['text'])
