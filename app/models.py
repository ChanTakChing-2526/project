from datetime import datetime, timedelta, timezone
from hashlib import md5
from app import app, db, login
import jwt, uuid


from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship('Booking', backref='customer', lazy='dynamic')

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

# ====================== 電影 ======================
class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    moviename = db.Column(db.String(128), index=True, unique=True)
    runtime = db.Column(db.Integer)
    category = db.Column(db.String(8))
    language = db.Column(db.String(100))
    releasedate = db.Column(db.Integer, index=True)
    poster_url = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    formats = db.Column(db.JSON)
    is_festival = db.Column(db.Boolean, default=False)

    # Relationships
    events = db.relationship('Event', secondary='movie_event', back_populates='movies')
    showtimes = db.relationship('Showtimes', back_populates='movie', lazy='select')

    def __repr__(self):
        return f'<Movie {self.moviename}>'


# ====================== 中間表 ======================
movie_event = db.Table('movie_event',
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True)
)


# ====================== 活動 ======================
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, index=True)   # ← 新增呢行
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    banner_image = db.Column(db.String(300))

    movies = db.relationship('Movie', secondary='movie_event',
                             back_populates='events')

    def __repr__(self):
        return f'<Event {self.title}>'

    # 自動生成 slug
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.title and not self.slug:
            from slugify import slugify
            self.slug = slugify(self.title, allow_unicode=True)


# ====================== 戲院 ======================
class Cinema(db.Model):
    __tablename__ = 'cinema'
    id = db.Column(db.Integer, primary_key=True)
    cinemaname = db.Column(db.String(128), index=True, unique=True)
    region = db.Column(db.String(5))
    address = db.Column(db.String(256))
    image_url = db.Column(db.String(256))

    halls = db.relationship('Halls', backref='cinema', lazy='dynamic')
    
    # 修改這裡：使用 back_populates 而唔係 backref
    showtimes = db.relationship('Showtimes', back_populates='cinema', lazy='dynamic')

    def __repr__(self):
        return f'<Cinema {self.cinemaname}>'


# ====================== 影廳 ======================
class Halls(db.Model):
    __tablename__ = 'halls'
    id = db.Column(db.Integer, primary_key=True)
    cinema_id = db.Column(db.Integer, db.ForeignKey('cinema.id'), nullable=False)
    hallname = db.Column(db.String(50))

    # 修改這裡：改用 back_populates
    showtimes = db.relationship('Showtimes', back_populates='hall', lazy='dynamic')
    seats = db.relationship('Seats', backref='hall', lazy='dynamic')

    def __repr__(self):
        return f'<Halls {self.hallname}>'


# ====================== 場次 (Showtimes) - 已改善 ======================
class Showtimes(db.Model):
    __tablename__ = 'showtimes'
    id = db.Column(db.Integer, primary_key=True)
    
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    cinema_id = db.Column(db.Integer, db.ForeignKey('cinema.id'), nullable=False)
    hall_id = db.Column(db.Integer, db.ForeignKey('halls.id'), nullable=False)
    
    day= db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    format_type = db.Column(db.String(50))
    price_base = db.Column(db.Float, nullable=False)

    # Relationships
    movie = db.relationship('Movie', back_populates='showtimes')
    cinema = db.relationship('Cinema', back_populates='showtimes')
    hall = db.relationship('Halls', back_populates='showtimes')   # ← 改成 back_populates
    def __repr__(self):
        return f'<Showtime {self.movie.moviename if self.movie else "Unknown"} at {self.start_time}>'


# ====================== 座位 ======================
class Seats(db.Model):
    __tablename__ = 'seats'
    id = db.Column(db.Integer, primary_key=True)
    hall_id = db.Column(db.Integer, db.ForeignKey('halls.id'), nullable=False)
    row_code = db.Column(db.String(5))
    seat_number = db.Column(db.Integer)
    is_booked = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Seat {self.row_code}{self.seat_number}>'


# ====================== 訂票相關 ======================
class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    showtime_id = db.Column(db.Integer, db.ForeignKey('showtimes.id'), nullable=False)
    total_price = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    
    showtime = db.relationship('Showtimes', backref='bookings')

    def __repr__(self):
        return f'<Booking {self.id}>'


class Tickets(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=False)
    ticket_code = db.Column(db.String(50), unique=True)

    booking = db.relationship('Booking', backref='tickets')
    seat = db.relationship('Seats', backref='tickets')

    def __repr__(self):
        return f'<Ticket {self.ticket_code}>'