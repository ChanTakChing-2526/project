from datetime import datetime, timedelta, timezone
from hashlib import md5
from app import app, db, login
import jwt


from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode({"reset_password": self.id,
                           "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)},
                          app.config["SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config["SECRET_KEY"], algorithms="HS256")[
                "reset_password"]
        except:           
            return None
        return User.query.get(id)
    
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    moviename = db.Column(db.String(128), index=True, unique=True)
    runtime = db.Column(db.Integer)
    category = db.Column(db.String(8))
    language = db.Column(db.String(30))
    releasedate = db.Column(db.Integer, index=True)
    poster_url = db.Column(db.String(256))
    formats = db.Column(db.JSON)

    # === 與活動的多對多關聯 ===
    events = db.relationship('Event', secondary='movie_event',
                             back_populates='movies')

    def __repr__(self):
        return f'<Movie {self.moviename}>'


class Cinema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cinemaname = db.Column(db.String(128), index=True, unique=True)


# ====================== 活動功能 ======================
# 中間表（association table）—— 必須定義喺 Event 之前
movie_event = db.Table('movie_event',
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True)
)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    banner_image = db.Column(db.String(300))

    # 多對多關聯
    movies = db.relationship('Movie', secondary='movie_event',
                             back_populates='events')

    def __repr__(self):
        return f'<Event {self.title}>'