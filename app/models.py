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
    password_hash = db.Column(db.String(128))
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

class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), index=True, unique=True)
    runtime = db.Column(db.Integer)
    category = db.Column(db.String(8))
    language = db.Column(db.String(30))
    releasedate = db.Column(db.DateTime, index=True)
    poster_url = db.Column(db.String(256))
    is_active = db.Column(db.Boolean)

    showtimes = db.relationship('Showtimes', backref='movie', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<Movie {self.title}>'

class Cinema(db.Model):
    __tablename__ = 'cinema'
    id = db.Column(db.Integer, primary_key=True)
    cinemaname = db.Column(db.String(128), index=True, unique=True)
    address = db.Column(db.String(256))

    halls = db.relationship('Halls', backref='cinema', lazy='dynamic')
    
    def __repr__(self) -> str:
        return f'<Cinema {self.cinemaname}>'
    
class Halls(db.Model):
    __tablename__ = 'halls'
    id = db.Column(db.Integer, primary_key=True)
    cinema_id = db.Column(db.Integer, db.ForeignKey('cinema.id'), nullable=False)
    hallname = db.Column(db.String(50))

    showtimes = db.relationship('Showtimes', backref='hall', lazy='dynamic')
    seats = db.relationship('Seats', backref='hall', lazy='dynamic')
    
    def __repr__(self) -> str:
        return f'<Halls {self.hallname}>'
    
class Showtimes(db.Model):
    __tablename__ = 'showtimes'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    hall_id = db.Column(db.Integer, db.ForeignKey('halls.id'), nullable=False)
    start_time = db.Column(db.DateTime)
    price_base = db.Column(db.Float)
    
    def __repr__(self) -> str:
        return f'<Showtime {self.movie_id} at Hall {self.hall_id}>'

class Seats(db.Model):
    __tablename__ = 'seats'
    id = db.Column(db.Integer, primary_key=True)
    hall_id = db.Column(db.Integer, db.ForeignKey('halls.id'), nullable=False)
    row_code = db.Column(db.String(5))
    seat_number = db.Column(db.Integer)
    
    def __repr__(self) -> str:
        return f'<Seat {self.id}>'

class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    showtime_id = db.Column(db.Integer, db.ForeignKey('showtimes.id'), nullable=False) 
    total_price = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def create_booking(user_id, showtime_id, selected_seat_ids):
        for seat_id in selected_seat_ids:
            already_taken = Tickets.query.join(Booking).filter(
                Booking.showtime_id == showtime_id,
                Tickets.seat_id == seat_id,
                Booking.status != 'cancelled'
            ).first()

            if already_taken:
                return False, f"座位 {seat_id} 已被預訂，請重新選擇。"
        
        try:
            current_showtime = Showtimes.query.get(showtime_id)
            if not current_showtime:
                return False, "找不到該場次"
            
            calc_total = current_showtime.price_base * len(selected_seat_ids)

            new_booking = Booking(
                user_id=user_id,
                showtime_id=showtime_id,
                status='paid',
                total_price= calc_total
            )
            db.session.add(new_booking)
            db.session.flush()

            for s_id in selected_seat_ids:
                new_ticket = Tickets(
                    booking_id=new_booking.id,
                    seat_id=s_id,
                    ticket_code="TKT-" + str(uuid.uuid4())[:8] # 範例生成代碼
                )
                db.session.add(new_ticket)

            db.session.commit()
            return True, "booking succeffuly"

        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
            return False, "system error, please try again"

    def __repr__(self) -> str:
        return f'<Booking {self.id}>'

class Tickets(db.Model):
    __tablename__ = 'ticketing'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=False)
    ticket_code = db.Column(db.String(50))
    
    def __repr__(self) -> str:
        return f'<Tickeets {self.id}>'