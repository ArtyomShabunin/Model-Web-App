import quart.flask_patch

# from flask import Flask
from quart import Quart
from quart_cors import cors
from config import Config
from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate

app = Quart(__name__)
app = cors(app, allow_origin="*")
app.config.from_object(Config)
db = SQLAlchemy(app)

from app import routes, models
