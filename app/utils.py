import time
import base64
from flask_bcrypt import Bcrypt
from flask import render_template, url_for
import re
from datetime import datetime
import hashlib
from Cryptodome.Cipher import AES
from Cryptodome.Util import Padding
import base64
from flask_login import current_user
from config import Config
import pytz
import requests

def encrypt_text(input_text, key):
    encrypted_text = ""
    for char in input_text:
        encrypted_char = chr((ord(char) + key) % 256)
        encrypted_text += encrypted_char
    encoded_text = base64.b64encode(encrypted_text.encode()).decode()
    return encoded_text

def decrypt_text(encoded_text, key):
    decoded_text = base64.b64decode(encoded_text.encode()).decode()
    decrypted_text = ""
    for char in decoded_text:
        decrypted_char = chr((ord(char) - key) % 256)
        decrypted_text += decrypted_char
    return decrypted_text

def hash_password(password):
    bcrypt = Bcrypt()
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    return password_hash

def check_password(password, password_hash):
    bcrypt = Bcrypt()
    return bcrypt.check_password_hash(password_hash, password)


def get_iso_time():
    current_time = datetime.utcnow().isoformat()
    return current_time[:-3] + 'Z'  # Remove microseconds and append 'Z' for UTC timezone


def render_dynamic_template(template_name, replacements=None, **kwargs):
    template = render_template(template_name, **kwargs)



    if not current_user.is_anonymous:
        user_joined_on = format_created_time(current_user.created_time)
        user_id = current_user.userId
        username = current_user.username
        profile_photo = current_user.profile_photo
    else:
        user_joined_on = "N/A"
        user_id = "00000000"
        username = "anonymous"
        profile_photo = url_for('static', filename='img/user.svg')

    standard_replacements = {
        "[USER_JOINED_ON]": user_joined_on,
        "[USERID]": user_id,
        "[USERNAME]": username,
        "[PROFILE_PHOTO]": profile_photo
    }

    for placeholder, value in standard_replacements.items():
        template = template.replace(placeholder, value)

    
    if replacements:
        for placeholder, value in replacements.items():
            if value is not None:
                template = template.replace(placeholder, value)

    return template


def is_valid_time(timestamp, time_offset):
    current_time = time.time()
    return (
        float(timestamp) -
        time_offset <= current_time <= float(timestamp) + time_offset
    )


def text_to_slug(text):
    
    slug = text.lower()
    # Remove special characters except hyphens and underscores
    slug = re.sub(r'[^a-z0-9-_\s]', '', slug)
    
    # Replace spaces with hyphens
    slug = slug.replace(' ', '-')
    
    # Remove multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Remove leading and trailing hyphens
    slug = slug.strip('-')
    
    return slug



def slug_to_text(slug):
    # Replace hyphens with spaces
    text = slug.replace('-', ' ')
    
    # Convert text to title case
    text = text.title()
    
    # Replace underscores with spaces
    text = text.replace('_', ' ')
    
    return text



def format_created_time(created_time_iso):
    # Parse the ISO 8601 date string to a datetime object
    created_time = datetime.strptime(created_time_iso, "%Y-%m-%dT%H:%M:%S.%fZ")
    
    # Convert to UTC timezone
    created_time_utc = created_time.replace(tzinfo=pytz.utc)
    
    # Convert to Kolkata timezone
    kolkata_tz = pytz.timezone('Asia/Kolkata')
    created_time_kolkata = created_time_utc.astimezone(kolkata_tz)
    
    # Format the datetime object to a desired string format
    formatted_time = created_time_kolkata.strftime('%B %d, %Y at %I:%M %p')
    
    return formatted_time



def generate_sha256_hash(word):
    
    return hashlib.sha256(word.encode()).hexdigest()


def compare_hashes(word, stored_hash):
    
    computed_hash = generate_sha256_hash(word)
    return computed_hash == stored_hash



#The below encrypt and decrypt functions uses pycryptodome which is a better way to encrypt and decrypt data and is used in database to store diary title and description. The encrypt_text and decrypt_text functions just uses base64 since we don't want any special characters as they will be used in the API query param.

def encrypt(data):
        cipher = AES.new(Config.AES_SECRET, AES.MODE_CBC, iv=bytes([0] * 16))
        encrypted = cipher.encrypt(
            Padding.pad(data.encode(), 16)
        )
        return base64.b64encode(encrypted).decode()

def decrypt(data):
    try:
        cipher = AES.new(
            Config.AES_SECRET,
            AES.MODE_CBC,
            iv=bytes([0] * 16)
        )
        return Padding.unpad(cipher.decrypt(base64.b64decode(data)), 16).decode()
    
    except Exception as e:
        return data

#used to decrypt the diary_title and diary_description
def modify_diary_entries_response(data):
    for entry in data['data']:
        entry["diary_title"] = decrypt(entry["diary_title"])
        entry["diary_description"] = decrypt(entry["diary_description"])
    return data


def generate_tokens(text):
    words = text.lower().split()
    return [hashlib.sha256(word.encode()).hexdigest() for word in words]



def get_google_provider_cfg():
    return requests.get(Config.GOOGLE_DISCOVERY_URL).json()


def construct_api_additional_param(queries):
    query_string = "&".join(f"{key}={value}" for key, value in queries.items() if key is not None and value is not None)


    return f"?{query_string}" if query_string else ""