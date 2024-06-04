import random
from ..database import usersdb
from ..models import User
from flask import Blueprint, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from ..forms import LoginForm, SignupForm
from ..utils import (
    hash_password,
    render_dynamic_template,
    check_password,
    get_iso_time,
    get_google_provider_cfg
)
from ..auth import google_client
import json
import requests
from config import Config, USERS_DB_PROPS

auth = Blueprint("auth", __name__)


@auth.route("/login/google", methods=["GET", "POST"])
def google_login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = google_client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@auth.route("/login/google/callback")
def google_callback():
    
    code = request.args.get("code")

    if not code:
        flash("No code found in url param", "red")
        return render_dynamic_template("404.html")

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = google_client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )

    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(Config.GOOGLE_CLIENT_ID, Config.GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens
    google_client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = google_client.add_token(userinfo_endpoint)

    userinfo_response = requests.get(uri, headers=headers, data=body).json()

    google_username = userinfo_response['email'].split("@")[0]

    user_data = usersdb.execute(
                "SELECT * FROM users WHERE {} = '{}'".format(USERS_DB_PROPS.EMAIL, userinfo_response['email'])
            ).get("data")
    
    #If creds not in db then add in db (first time google login)

    if not len(user_data) >= 1:
        email = userinfo_response.get('email')
        password = hash_password("TEMP")
        userid = random.randint(10000000, 99999999)

        props = (USERS_DB_PROPS.EMAIL, USERS_DB_PROPS.USERNAME, USERS_DB_PROPS.PASSWORD, USERS_DB_PROPS.CATEGORIES, USERS_DB_PROPS.USERID, USERS_DB_PROPS.TOTAL_ENTRIES, USERS_DB_PROPS.SIGNUP_TYPE, USERS_DB_PROPS.PROFILE_PICTURE)

        usersdb.execute(
            "INSERT INTO users {} VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                props,
                email,
                google_username,
                password,
                "Daily",  # Default Category to be added for every new user
                userid, #random userId
                0,  # Starting with 0 as total entries for every new user
                "google", #type of signup
                userinfo_response.get('picture')
            )
        )


        user = User(
            google_username,
            password,
            userid,
            "Daily",
            get_iso_time(),
            profile_photo = userinfo_response.get('picture')
        )

        login_user(user, remember=True)

        return redirect(url_for("main.dashboard"))
    
    else:

        user_data = user_data[0]
        user = User(
            user_data.get('username'),
            user_data.get('password'),
            user_data.get('userid'),
            user_data.get('categories'),
            user_data.get('created_time'),
            
        )

        login_user(user, remember=True)


    return redirect(url_for("main.dashboard"))


@auth.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        form_username = form.username.data.strip()
        form_password = form.password.data.strip()
        remember = form.remember.data
        
        user_data = usersdb.execute(
            "SELECT * FROM users WHERE {} = '{}'".format(USERS_DB_PROPS.USERNAME, form_username)
        )

        if len(user_data.get("data")) >= 1:

            user_data = user_data.get("data")[0]

            if check_password(form_password, user_data.get("password")):
                user = User(
                    user_data.get("username"),
                    user_data.get("password"),
                    user_data.get("userid"),
                    user_data.get("categories"),
                    user_data.get("created_time")
                )
                login_user(user, remember=remember)

                return redirect(url_for("main.dashboard"))

            else:
                flash("Invalid username or password", "red")

        flash("Invalid username or password", "red")

    replacements = {
        "[PAGE_INFO]": "Login",
    }

    return render_dynamic_template("login.html", replacements=replacements, form=form)


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    page_info = "Signup"

    if form.validate_on_submit():
        form_email = form.email.data.strip()
        form_username = form.username.data.strip()
        form_password1 = form.password1.data.strip()
        form_password2 = form.password2.data.strip()

        if form_password1 != form_password2:
            flash("Passwords didn't match. Please try again.", "red")
        else:
            user_data = usersdb.execute(
                "SELECT * FROM users WHERE {} = '{}'".format(USERS_DB_PROPS.EMAIL, form_email)
            ).get("data")

            if len(user_data) >= 1:

                if user_data[0].get(USERS_DB_PROPS.SIGNUP_TYPE) == "google":
                    flash("You have already used this email in Google Login. Please use Google Login to continue", "red")

                else:
                    flash("Email already exists. Please choose another username.", "red")
                
                flash("Email already exists. Please choose another username.", "red")
            else:
                try:
                    props = (USERS_DB_PROPS.EMAIL, USERS_DB_PROPS.USERNAME, USERS_DB_PROPS.PASSWORD, USERS_DB_PROPS.CATEGORIES, USERS_DB_PROPS.USERID, USERS_DB_PROPS.TOTAL_ENTRIES, USERS_DB_PROPS.SIGNUP_TYPE)

                    usersdb.execute(
                        "INSERT INTO users {} VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                            props,
                            form_email,
                            form_username,
                            hash_password(form_password1),
                            "Daily",  # Default Category to be added for every new user
                            random.randint(10000000, 99999999), #random userId
                            0,  # Starting with 0 as total entries for every new user
                            "site" #type of signup since it is using site
                        )
                    )
                except Exception as e:
                    print(e)
                    flash("Error adding user", "red")
                else:
                    flash(
                        "You have successfully signed up! You can now log in.", "green"
                    )
                    return redirect(url_for("auth.login"))

    replacements = {
        "[PAGE_INFO]": page_info,
    }

    return render_dynamic_template("signup.html", form=form, replacements=replacements)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
