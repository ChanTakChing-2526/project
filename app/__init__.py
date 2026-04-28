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
    
    from app.models import Movie
    if Movie.query.count() == 0:
        print("🔄 偵測到資料庫為空，正在自動初始化測試資料（首次啟動）...")
        import all_data  # 自動執行清空 + 插入所有測試資料
        print("✅ 資料庫初始化完成！")