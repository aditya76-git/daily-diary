import time
from flask_login import UserMixin
from config import Config
from .utils import encrypt_text

class User(UserMixin):
    def __init__(self, username, password, userId, categories, created_time, profile_photo = None):
        self.id = username
        self.username = username
        self.password = password
        self.encrypted_username = encrypt_text(
            username + Config.SEPERATOR + str(time.time()), Config.KEY
        )
        self.userId = userId
        self.categories = categories.split("+")
        self.created_time = created_time  
        self.profile_photo = profile_photo  
