# auth.py
from functools import wraps
from flask import redirect, url_for
from flask_login import LoginManager, current_user
from .database import usersdb
from .models import User
from oauthlib.oauth2 import WebApplicationClient
from config import Config, USERS_DB_PROPS

login_manager = LoginManager()
google_client = WebApplicationClient(Config.GOOGLE_CLIENT_ID)


def login_required(view):
    @wraps(view)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return decorated_view

@login_manager.user_loader
def load_user(username):
    
    user_data = usersdb.execute("SELECT * FROM users WHERE {} = '{}'".format(USERS_DB_PROPS.USERNAME, username))
    user_data = user_data.get('data')[0]
    
    if user_data:
        diary_username = user_data.get("username")
        diary_password = user_data.get("password")
        return User(diary_username, diary_password, user_data.get('userid'), user_data.get('categories'), user_data.get('created_time'), profile_photo = user_data.get('profile_picture'))
    return None

