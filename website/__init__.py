from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_share import Share
from flask_caching import Cache
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()

base_dir = os.path.dirname(os.path.realpath(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(base_dir, 'scissor.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

share = Share(app)
cache = Cache(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

from . import routes
from .models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)