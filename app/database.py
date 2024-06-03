from pynotiondb import NOTION_API
from config import Config

usersdb = NOTION_API(Config.NOTION_API_SECRET, Config.USERS_DB_ID)
entriesdb = NOTION_API(Config.NOTION_API_SECRET, Config.ENTRIES_DB_ID)