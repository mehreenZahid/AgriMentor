from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth

bcrypt = Bcrypt()
login_manager = LoginManager()
oauth = OAuth()