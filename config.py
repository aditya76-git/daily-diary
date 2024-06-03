
class Config:
    #The key which is used to encrypt the username and other info which will be used in API so that it becomes difficult for other developers to guess the complete API url.
    KEY = 0000 

    #Flask App Secret Key
    APP_SECRET_KEY = ""
    
    #The time in seconds after which the API returns a access deined error
    TIME_OFFEST = 60

    SEPERATOR = "__"

    NOTION_API_SECRET = ""

    USERS_DB_ID = ""

    ENTRIES_DB_ID = ""

    #This key is used to encryt and decrypt diary title and diary description. Make sure it is of the length 16.

    #random_key = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(16))
    
    #The above code can be used to generate a key
    AES_SECRET = b''

    GOOGLE_CLIENT_ID = ""
    GOOGLE_CLIENT_SECRET = ""
    GOOGLE_DISCOVERY_URL = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )

class USERS_DB_PROPS:
    # These are going to be the properties which are in the notiondb for users database, you can modify this according to the properties you have made inside the notion database
    EMAIL = "email" #text
    
    USERID = "userid" #text
    
    USERNAME = "username" #text
    
    PASSWORD = "password" #text
    
    CATEGORIES = "categories" #text
    
    TOTAL_ENTRIES = "total_entries" #number
    
    SIGNUP_TYPE = "signup_type" #text
    
    PROFILE_PICTURE = "profile_picture" #text


class ENTRIES_DB_PROPS:
    # These are going to be the properties which are in the notiondb for entries database, you can modify this according to the properties you have made inside the notion database
    USERNAME = "username" #text
    
    DIARY_TITLE = "diary_title" #text
    
    DIARY_DESCRIPTION = "diary_description" #text
    
    EMOJI = "emoji" #text
    
    CATEGORY = "category" #text
    
    SHARING = "sharing" #text
    
    SLUG = "slug" #text
    
    POSTID = "postid" #text
    
    DIARY_TITLE_SEARCH_TOKEN = "diary_title_search_token" #text
    
    DAY = "day" #number
    
    MONTH = "month" #number

    YEAR = "year" #number
