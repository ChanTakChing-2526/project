from datetime import date
from flask import render_template, redirect, flash, url_for, request, jsonify
from collections import defaultdict
from flask_login import current_user, login_user, logout_user
from urllib.parse import urlparse
import uuid

from app import app, db
from app.models import Movie, Event, Cinema, Showtimes, User, Booking, Tickets, Seats, GiftCard
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.email import send_password_reset_email

@app.route("/", methods=['GET', 'POST'])
@app.route("/index")
def index():
    movies = Movie.query.filter_by(is_active=True).all() 
    return render_template("index.html.j2", show_secondary_navbar=False, title="Home", movies = movies)

@app.route('/upcoming')
def upcoming():
    movies = Movie.query.filter_by(is_active=False).all()
    return render_template('upcoming.html.j2', show_secondary_navbar=True, movies=movies, page_title="Coming Soon")

@app.route('/cinema')
def cinemas():
    all_cinemas = Cinema.query.all()
    
    cinema_dict = defaultdict(list)
    for c in all_cinemas:
        cinema_dict[c.region].append(c)
        
    return render_template('cinema.html.j2', show_secondary_navbar=True, title='Cinema Locations', cinema_dict=cinema_dict)

@app.route('/cinema/<int:id>')
def cinema_detail(id):
    cinema = Cinema.query.get_or_404(id)
    showtimes = cinema.showtimes.order_by(Showtimes.movie_id, Showtimes.start_time).all()

    print(f"DEBUG: 查到的影院ID: {id}")
    print(f"DEBUG: 查到的場次數量: {len(showtimes)}")
    print(f"DEBUG: 場次資料: {showtimes}")
    
    return render_template('cinema_detail.html.j2', show_secondary_navbar=True, cinema=cinema, showtimes=showtimes)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password!')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get("next")
        if not next_page or urlparse(next_page).netloc != "":
            next_page = url_for('index')
        return redirect(next_page) 
        
    return render_template('login.html.j2', show_secondary_navbar=True, title="Sign In", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data, 
            given_name=form.given_name.data,
            surname=form.surname.data,
            gender=form.gender.data
        )
        
        user.set_password(form.password.data)
        
        user.birth_date = date(
            int(form.year.data), 
            int(form.month.data), 
            int(form.day.data)
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
        
    return render_template('register.html.j2', show_secondary_navbar=True, title="Register", form=form)

@app.route("/reset_password_request", methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset password.')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html.j2', show_secondary_navbar=True, title="Reset Password", form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    print(f"DEBUG: 系統已收到請求，Token 為: {token}")
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if user is None:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html.j2', show_secondary_navbar=True, title="Reset Password", form=form)

@app.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    bookings = user.bookings.order_by(Booking.created_at.desc()).paginate(
        page=page, per_page=app.config.get('POSTS_PER_PAGE', 10), error_out=False)
    
    next_url = url_for('user', username=user.username, page=bookings.next_num) \
        if bookings.has_next else None
    prev_url = url_for('user', username=user.username, page=bookings.prev_num) \
        if bookings.has_prev else None

    return render_template('user.html.j2', show_secondary_navbar=True, user=user, bookings=bookings.items,next_url=next_url,prev_url=prev_url)

@app.route('/events')
def events_list():
    events = Event.query.order_by(Event.start_date.desc()).all()
    return render_template('events_list.html.j2', show_secondary_navbar=True, events=events)


@app.route('/events/<string:slug>')
def event_detail(slug):
    event = Event.query.filter_by(slug=slug).first_or_404()
    return render_template('movie_list.html.j2', show_secondary_navbar=True, movies=event.movies, page_title=event.title, current_filter=None)

@app.route('/ticket_select/<int:showtime_id>')
def ticket_select(showtime_id):
    if not current_user.is_authenticated:
        flash('請先登入才能購票', 'danger')
        return redirect(url_for('login'))
    
    showtime = Showtimes.query.get_or_404(showtime_id)
    seats = showtime.hall.seats.order_by(Seats.row_code, Seats.seat_number).all()
    
    return render_template('seat_select.html.j2', show_secondary_navbar=True, showtime=showtime, seats=seats)

@app.route('/book_tickets', methods=['POST'])
def book_tickets():
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "請先登入才能購票"})

    data = request.get_json()
    showtime_id = data.get('showtime_id')
    seat_ids = data.get('seat_ids', [])

    if not seat_ids:
        return jsonify({"success": False, "message": "請至少選擇一個座位"})

    showtime = Showtimes.query.get_or_404(showtime_id)
    total_price = len(seat_ids) * 80 

    if current_user.points < total_price:
        return jsonify({"success": False, "message": f"積分不足！需要 {total_price} 分，你只有 {current_user.points} 分"})

    booking = Booking(
        user_id = current_user.id,
        showtime_id = showtime_id,
        total_price = total_price,
        status = 'paid'
    )
    db.session.add(booking)
    db.session.flush()

    for seat_id in seat_ids:
        ticket = Tickets(
            booking_id = booking.id,
            seat_id = seat_id,
            ticket_code = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        )
        db.session.add(ticket)

        seat = Seats.query.get(seat_id)
        if seat:
            seat.is_booked = True

    current_user.points -= total_price

    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"購票成功！已扣除 {total_price} 積分，購買 {len(seat_ids)} 張票"
    })

@app.route("/gift_card", methods=["GET", "POST"])
def gift_card():
    error = None

    if request.method == "POST":
        card_number = request.form.get("card_number")
        pin = request.form.get("pin")

        setup_card_number = request.form.get("setup_card_number")

        if card_number and pin:
            card = GiftCard.query.filter_by(card_number=card_number).first()
            if card and str(card.pin) == pin:
                flash(f"卡號 {card_number} 餘額: HK$ {card.balance:.2f}", "success")
            else:
                error = "無效的禮品卡號或密碼。"

        elif setup_card_number:
            if not current_user.is_authenticated:
                error = "請先登入以設定禮品卡密碼"
            else:
                card = GiftCard.query.filter_by(card_number=setup_card_number).first()
                if card:
                    card.pin = str(current_user.id)
                    db.session.commit()
                    flash("Top-up successful", "success")
                else:
                    error = "無效的禮品卡號"

    return render_template("gift_card.html.j2", show_secondary_navbar=True, error=error, title="Gift Card")