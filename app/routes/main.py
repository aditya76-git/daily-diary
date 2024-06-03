from ..database import entriesdb, usersdb
from flask import Blueprint, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from ..forms import EntryForm
from ..utils import (
    render_dynamic_template,
    text_to_slug,
    slug_to_text,
    format_created_time,
    encrypt,
    decrypt,
    generate_tokens,
    construct_api_additional_param
)
from datetime import datetime
import uuid
from config import ENTRIES_DB_PROPS, USERS_DB_PROPS

main = Blueprint("main", __name__)

@main.route("/", methods=["GET"])
def home():
    # print(current_user.profile_photo)
    return jsonify(
        {
            "message" : "Hello and welcome to Daily Diary. Home page is still left to be added. You can login and visit /dashboard"
        }
    )
    
    
    

@main.route("/dashboard", methods=["GET"])
@login_required
def dashboard():

    active_page = "dashboard"
    page_info = "Dashboard"

    replacements = {
        "[PAGE_INFO]": page_info,
        "[NAVBAR_TITLE]": page_info,  # Will be used to add in navbar.html
    }
    
    queries = {
        "search_query" : request.args.get("s"),
        "year" : request.args.get("year"),
        "month" : request.args.get("month"),
        "day" : request.args.get("day")
    }

    additional_param = construct_api_additional_param(queries)

    return render_dynamic_template(
        "dashboard.html",
        replacements=replacements,
        active_page=active_page,
        encrypted_username=current_user.encrypted_username,
        categories=current_user.categories,
        additional_param=additional_param,
        created_time=current_user.created_time
    )


@main.route("/category/<category_name>", methods=["GET"])
@login_required
def category(category_name):

    category_name = slug_to_text(category_name)

    search_query = request.args.get("s")

    page_info = "Category - {}".format(category_name)

    replacements = {
        "[PAGE_INFO]": page_info,
        "[NAVBAR_TITLE]": page_info,  # Will be used to add in navbar.html
    }

    queries = {
        "category" : category_name,
        "search_query" : search_query
    }

    additional_param = construct_api_additional_param(queries)

    return render_dynamic_template(
        "dashboard.html",
        replacements=replacements,
        encrypted_username=current_user.encrypted_username,
        categories=current_user.categories,
        additional_param=additional_param,
        created_time=current_user.created_time,
    )



@main.route("/access/<access_value>", methods=["GET"])
@login_required
def access(access_value):

    search_query = request.args.get("s")
    page_info = "{} entries".format(access_value.upper())

    replacements = {
        "[PAGE_INFO]": page_info,
        "[NAVBAR_TITLE]": page_info,  # Will be used to add in navbar.html
    }
    queries = {
        "search_query" : search_query,
        "access" : access_value
    }

    additional_param = construct_api_additional_param(queries)

    return render_dynamic_template(
        "dashboard.html",
        replacements=replacements,
        encrypted_username=current_user.encrypted_username,
        categories=current_user.categories,
        additional_param=additional_param,
        created_time=current_user.created_time,
    )


@main.route("/create", methods=["GET", "POST"])
@login_required
def add_entry():

    active_page = "add-entry"
    page_info = "Add Entry"
    diary_title = None
    postid = None

    form = EntryForm()
    form.user_categories.choices = [(cat, cat) for cat in current_user.categories]

    if form.validate_on_submit():

        diary_title = form.title.data
        desc = form.description.data
        emoji = form.emoji.data
        sharing = form.sharing.data
        categories = form.user_categories.data

        try:
            postid = str(uuid.uuid4())
            now = datetime.now()
            diary_title_search_token = generate_tokens(diary_title.strip())
            diary_title_search_token = ",".join(diary_title_search_token)
            props = (ENTRIES_DB_PROPS.USERNAME, ENTRIES_DB_PROPS.DIARY_TITLE, ENTRIES_DB_PROPS.DIARY_DESCRIPTION, ENTRIES_DB_PROPS.EMOJI, ENTRIES_DB_PROPS.CATEGORY, ENTRIES_DB_PROPS.SHARING, ENTRIES_DB_PROPS.SLUG, ENTRIES_DB_PROPS.POSTID, ENTRIES_DB_PROPS.DIARY_TITLE_SEARCH_TOKEN, ENTRIES_DB_PROPS.YEAR, ENTRIES_DB_PROPS.MONTH, ENTRIES_DB_PROPS.DAY)

            query = "INSERT INTO entries {} VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                props,
                current_user.username,
                encrypt(diary_title),
                encrypt(desc),
                emoji,
                "+".join(categories) if categories is not None else "Daily",
                sharing.lower(),
                text_to_slug(diary_title),
                postid,
                diary_title_search_token,
                now.year,
                now.month,
                now.day,
            )

            entriesdb.execute(query)
            flash("Entry added successfully", "green")
        except Exception as e:
            flash("Something went wrong posting", "red")
            print(e)

    replacements = {
        "[PAGE_INFO]": page_info,
        "[NAVBAR_TITLE]": page_info,  # Will be used to add in navbar.html
        "[POSTID]": postid,  # Will be used to add in add-entry.html for postid
        "[FORM_ACTION]": url_for("main.add_entry"),
    }

    return render_dynamic_template(
        "form-entry.html",
        replacements=replacements,
        active_page=active_page,
        categories=current_user.categories,
        form=form,
    )


@main.route("/view/<postid>", methods=["GET"])
def view_entry(postid):
    active_page = None

    post_data = entriesdb.execute(
        "SELECT * FROM users WHERE {} = '{}'".format(ENTRIES_DB_PROPS.POSTID, postid)
    )

    if not post_data.get("data"):
        flash("Post not found!", "red")
        return render_dynamic_template("404.html")

    post_data = post_data["data"][0]

    if post_data.get("sharing") != "public" and not current_user.is_authenticated:
        flash("Access Denied. Private post", "red")
        return render_dynamic_template("404.html")

    page_info = decrypt(post_data.get("diary_title"))

    if post_data.get("sharing") == "private":

        replacements = {
            "[PAGE_INFO]": page_info,
            "[NAVBAR_TITLE]": "",  # Will be used to add in navbar.html
            "[POST_CREATED_TIME]": format_created_time(
                post_data.get("last_edited_time")
            ),
            "[POST_DESCRIPTION]": decrypt(post_data.get("diary_description")).replace('\r\n', '<br>').replace('\n', '<br>'),
            "[POST_TITLE]": decrypt(post_data.get("diary_title")),
            "[POST_EMOJI]": post_data.get("emoji"),
        }

    else:
        replacements = {
            "[POST_CREATED_TIME]": format_created_time(
                post_data.get("last_edited_time")
            ),
            "[NAVBAR_TITLE]": "",  # Will be used to add in navbar.html
            "[PAGE_INFO]": page_info,
            "[POST_DESCRIPTION]": decrypt(post_data.get("diary_description")).replace('\r\n', '<br>').replace('\n', '<br>'),
            "[POST_TITLE]": decrypt(post_data.get("diary_title")),
            "[POST_EMOJI]": post_data.get("emoji"),
        }

    template_name = (
        "view-entry.html" if current_user.is_authenticated else "view-entry-public.html"
    )
    
    return render_dynamic_template(
        template_name,
        replacements=replacements,
        active_page=active_page,
        encrypted_username=current_user.encrypted_username
        if not current_user.is_anonymous
        else "",
        categories=current_user.categories if not current_user.is_anonymous else "",
        postid=postid,
    )


@main.route("/<username>/<post_slug>", methods=["GET"])
def post_slug_view_entry(username, post_slug):
    active_page = None

    post_data = entriesdb.execute(
        "SELECT * FROM users WHERE {} = '{}' AND {} = {}".format(ENTRIES_DB_PROPS.USERNAME, username, ENTRIES_DB_PROPS.SLUG, post_slug)
    )

    if not post_data.get("data"):
        flash("Post not found!", "red")
        return render_dynamic_template("404.html")

    post_data = post_data["data"][0]

    if post_data.get("sharing") != "public" and not current_user.is_authenticated:
        flash("Access Denied. Private post", "red")
        return render_dynamic_template("404.html")

    page_info = decrypt(post_data.get("diary_title"))

    if post_data.get("sharing") == "private":

        replacements = {
            "[PAGE_INFO]": page_info,
            "[NAVBAR_TITLE]": "",  # Will be used to add in navbar.html
            "[POST_CREATED_TIME]": format_created_time(
                post_data.get("last_edited_time")
            ),
            "[POST_DESCRIPTION]": decrypt(post_data.get("diary_description")).replace('\r\n', '<br>').replace('\n', '<br>'),
            "[POST_TITLE]": decrypt(post_data.get("diary_title")),
            "[POST_EMOJI]": post_data.get("emoji"),
        }

    else:
        user_data = usersdb.execute(
        "SELECT * FROM users WHERE {} = '{}'".format(USERS_DB_PROPS.USERNAME, username)
    )
        user_data = user_data['data'][0]
        replacements = {
            "[PROFILE_PHOTO]" : user_data.get('profile_picture'),
            "[POST_CREATED_TIME]": format_created_time(
                post_data.get("last_edited_time")
            ),
            "[NAVBAR_TITLE]": "",  # Will be used to add in navbar.html
            "[PAGE_INFO]": page_info,
            "[POST_DESCRIPTION]": decrypt(post_data.get("diary_description")).replace('\r\n', '<br>').replace('\n', '<br>'),
            "[POST_TITLE]": decrypt(post_data.get("diary_title")),
            "[POST_EMOJI]": post_data.get("emoji"),
        }

    template_name = (
        "view-entry.html" if current_user.is_authenticated else "view-entry-public.html"
    )
    
    return render_dynamic_template(
        template_name,
        replacements=replacements,
        active_page=active_page,
        encrypted_username=current_user.encrypted_username
        if not current_user.is_anonymous
        else "",
        categories=current_user.categories if not current_user.is_anonymous else "",
        postid=post_data.get("postid"),
    )


@main.route("/edit/<postid>", methods=["GET", "POST"])
@login_required
def edit_entry(postid):

    active_page = None
    page_info = "Edit Entry"

    post_data = entriesdb.execute(
        "SELECT * FROM users WHERE {} = '{}'".format(ENTRIES_DB_PROPS.POSTID, postid)
    )

    if not post_data.get("data"):
        flash("The post doesn't exist!", "red")
        return render_dynamic_template("404.html")

    post_data = post_data["data"][0]

    form = EntryForm()
    form.user_categories.choices = [(cat, cat) for cat in current_user.categories]

    if request.method == "POST":

        if form.validate_on_submit():

            title = form.title.data
            description = form.description.data
            emoji = form.emoji.data
            user_categories = (
                "+".join(form.user_categories.data)
                if form.user_categories.data is not None
                else "Daily"
            )

            sharing = form.sharing.data

            query = "UPDATE entries SET "
            query += "{} = '{}' AND ".format(ENTRIES_DB_PROPS.DIARY_TITLE, encrypt(title.strip()))
            query += "{} = '{}' AND ".format(ENTRIES_DB_PROPS.DIARY_DESCRIPTION, encrypt(description.strip()))
            query += "{} = '{}' AND ".format(ENTRIES_DB_PROPS.EMOJI, emoji.strip())
            query += "{} = '{}' AND ".format(ENTRIES_DB_PROPS.CATEGORY, user_categories)
            query += "{} = '{}' AND ".format(ENTRIES_DB_PROPS.SHARING, sharing.lower())
            query += "{} = '{}' ".format(ENTRIES_DB_PROPS.SLUG, text_to_slug(title))
            query += "WHERE {} = '{}'".format(ENTRIES_DB_PROPS.POSTID, postid)

            entriesdb.execute(query)


            return redirect(url_for("main.view_entry", postid=postid))


    else:

        form.title.data = decrypt(post_data["diary_title"])
        form.description.data = decrypt(post_data["diary_description"])
        form.emoji.data = post_data["emoji"]
        form.user_categories.data = post_data["category"].split("+")
        form.sharing.default = post_data["sharing"]

    replacements = {
        "[PAGE_INFO]": page_info,
        "[NAVBAR_TITLE]": page_info,  # Will be used to add in navbar.html
        "[POSTID]": postid,  # Will be used to add in add-entry.html for postid
        "[FORM_ACTION]": url_for("main.edit_entry", postid=postid),
    }

    return render_dynamic_template(
        "form-entry.html",
        replacements=replacements,
        active_page=active_page,
        categories=current_user.categories,
        form=form,
    )

