# __init__.py
from flask import Flask
from flask_cors import CORS
from .auth import login_manager
from .routes.main import main as main_blueprint
from .routes.api import api as api_blueprint
from .routes.auth import auth as auth_blueprint
from .utils import render_dynamic_template
from config import Config

app = Flask(__name__)
CORS(app)


@app.errorhandler(404)
def page_not_found(error):

    replacements = {
        "[PAGE_INFO]": "404 Page not Found",
    }
    return render_dynamic_template('404.html', replacements = replacements), 404

app.config.from_object('config.Config')
app.secret_key = Config.APP_SECRET_KEY
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

app.register_blueprint(main_blueprint)
app.register_blueprint(api_blueprint)
app.register_blueprint(auth_blueprint)

