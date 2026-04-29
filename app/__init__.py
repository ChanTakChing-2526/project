import os
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler

from flask import Flask
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment

DISABLE_DB = os.environ.get("DISABLE_DB") == "true"

db = SQLAlchemy()
login = LoginManager()
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    login.login_view = "login"
    login.init_app(app)

    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)

    if not DISABLE_DB:
        db.init_app(app)
        Migrate(app, db)

        with app.app_context():
            db.create_all()

            from app.models import User
            if User.query.count() == 0:
                print("🔄 首次啟動，自動建立測試用戶...")
                from all_data import create_test_users_only
                create_test_users_only()
                print("✅ 測試用戶建立完成！")
    else:
        print("🚫 Cloud Run 環境：已停用資料庫功能")

    from app.routes import routes_bp
    app.register_blueprint(routes_bp)

    from app.movies import movies_bp
    app.register_blueprint(movies_bp)

    return app
