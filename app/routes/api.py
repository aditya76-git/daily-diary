
from ..database import entriesdb
from flask import request, jsonify, Blueprint
from config import Config
from ..utils import (
    decrypt_text,
    is_valid_time,
    modify_diary_entries_response,
    generate_tokens
)
from config import ENTRIES_DB_PROPS

api = Blueprint("api", __name__)

@api.route("/api/get-entries/<encrypted_username>")
def api_get_entries(encrypted_username):
    decrypted_data = decrypt_text(encrypted_username, Config.KEY)
    username, timestamp = decrypted_data.split(Config.SEPERATOR)

    if is_valid_time(timestamp, Config.TIME_OFFEST):

        category = request.args.get("category")
        search_query = request.args.get("search_query") or request.args.get(
            "amp;search_query"
        )

        access_value = request.args.get("access")
        day_value = request.args.get("day")
        month_value = request.args.get("month")
        year_value = request.args.get("year")

        sql_query = "SELECT * from entries WHERE {} = {} ".format(ENTRIES_DB_PROPS.USERNAME, username)

        if category:
            sql_query += "AND {} LIKE {} ".format(ENTRIES_DB_PROPS.CATEGORY, category)

        if search_query:
            search_token = generate_tokens(search_query)
            search_token = ",".join(search_token)
            sql_query += "AND {} LIKE {} ".format(ENTRIES_DB_PROPS.DIARY_TITLE_SEARCH_TOKEN, search_token)


        if access_value:
            sql_query += "AND {} = {} ".format(ENTRIES_DB_PROPS.SHARING, access_value)

        if year_value:
            sql_query += "AND {} = {} ".format(ENTRIES_DB_PROPS.YEAR, year_value)

        if month_value:
            sql_query += "AND {} = {} ".format(ENTRIES_DB_PROPS.MONTH, month_value)

        if day_value:
            sql_query += "AND {} = {} ".format(ENTRIES_DB_PROPS.DAY, day_value)



        entries = entriesdb.execute(sql_query)

        return jsonify(modify_diary_entries_response(entries))

    return jsonify({"error": True, "message": "Access Denied"})

