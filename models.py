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


class Image:
    def __init__(self, url, category):
        self.url = url
        self.category = category


    def to_dict(self):
        return {
            'url': self.url,
            'category': self.category,
        }
    
    @staticmethod
    def from_dict(data):
        return Image(data['url'], data.get('category'))
