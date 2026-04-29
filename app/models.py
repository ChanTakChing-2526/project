from datetime import datetime, timedelta, timezone
from hashlib import md5
from app import app, db, login
import jwt, uuid

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    given_name = db.Column(db.String(64), nullable=False)
    surname = db.Column(db.String(64), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    points = db.Column(db.Integer, default=1000)
    bookings = db.relationship('Booking', backref='customer', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
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
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    moviename = db.Column(db.String(128), index=True, unique=True)
    runtime = db.Column(db.Integer)
    category = db.Column(db.String(32))
    language = db.Column(db.String(128))
    releasedate = db.Column(db.Date, index=True)
    poster_url = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    formats = db.Column(db.JSON)

    events = db.relationship('Event', secondary='movie_event', back_populates='movies')
    showtimes = db.relationship('Showtimes', back_populates='movie', lazy='dynamic')

    def __repr__(self):
        return f'<Movie {self.moviename}>'

movie_event = db.Table('movie_event',
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True)
)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, index=True)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    banner_image = db.Column(db.String(300))

    movies = db.relationship("Movie", secondary="movie_event", back_populates="events", cascade="all, delete")

    def __repr__(self):
        return f'<Event {self.title}>'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.title and not self.slug:
            from slugify import slugify
            self.slug = slugify(self.title, allow_unicode=True)

class Cinema(db.Model):
    __tablename__ = 'cinema'
    id = db.Column(db.Integer, primary_key=True)
    cinemaname = db.Column(db.String(128), index=True, unique=True)
    region = db.Column(db.String(5))
    address = db.Column(db.String(256))
    image_url = db.Column(db.String(256))

    halls = db.relationship('Halls', backref='cinema', lazy='dynamic')
    showtimes = db.relationship('Showtimes', back_populates='cinema', lazy='dynamic')

    def __repr__(self):
        return f'<Cinema {self.cinemaname}>'

class Halls(db.Model):
    __tablename__ = 'halls'
    id = db.Column(db.Integer, primary_key=True)
    cinema_id = db.Column(db.Integer, db.ForeignKey('cinema.id'), nullable=False)
    hallname = db.Column(db.String(50))

    showtimes = db.relationship('Showtimes', back_populates='hall', lazy='dynamic')
    seats = db.relationship('Seats', backref='hall', lazy='dynamic')

    def __repr__(self):
        return f'<Halls {self.hallname}>'

class Showtimes(db.Model):
    __tablename__ = 'showtimes'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    cinema_id = db.Column(db.Integer, db.ForeignKey('cinema.id'), nullable=False)
    hall_id = db.Column(db.Integer, db.ForeignKey('halls.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    format_type = db.Column(db.String(50))
    price_base = db.Column(db.Float, nullable=False)

    movie = db.relationship('Movie', back_populates='showtimes')
    cinema = db.relationship('Cinema', back_populates='showtimes')
    hall = db.relationship('Halls', back_populates='showtimes')
    def __repr__(self):
        return f'<Showtime {self.movie.moviename if self.movie else "Unknown"} at {self.start_time}>'

class Seats(db.Model):
    __tablename__ = 'seats'
    id = db.Column(db.Integer, primary_key=True)
    hall_id = db.Column(db.Integer, db.ForeignKey('halls.id'), nullable=False)
    row_code = db.Column(db.String(5))
    seat_number = db.Column(db.Integer)
    is_booked = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Seat {self.row_code}{self.seat_number}>'

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

class GiftCard(db.Model):
    __tablename__ = 'gift_card'
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(16), unique=True, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))   # ← 新增
    balance = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='gift_cards')

    def __repr__(self):
        return f'<GiftCard {self.card_number}>'
    


