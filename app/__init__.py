import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import os
from flask import Flask
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager()
login.login_view = "login"
login.init_app(app)
mail = Mail(app)
bootstrap = Bootstrap(app)
moment = Moment(app)

from app import models, routes
from app.movies import movies_bp
app.register_blueprint(movies_bp)

with app.app_context():
    db.create_all()
    
    from app.models import User
    if User.query.count() == 0:
        print("🔄 首次啟動，自動建立測試用戶（唔會影響現有資料）...")
        from all_data import create_test_users_only
        create_test_users_only()
        print("✅ 測試用戶建立完成！")
