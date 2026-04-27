from flask import render_template, redirect, flash, url_for, request, jsonify
from collections import defaultdict
from flask_login import current_user, login_user, logout_user
import uuid

from app import app, db
from app.models import (
    Movie, Cinema, Showtimes, User, Booking, Tickets, Seats, GiftCard
)
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.email import send_password_reset_email

# ====================== 基礎頁面路由 ======================
@app.route("/")
@app.route("/index")
def index():
    movies = Movie.query.filter_by(is_active=True).all() 
    return render_template("index.html.j2", title="Home", movies = movies)

#@app.route("/movies")
#def ticketing():
    #return render_template("movie_list.html.j2", itle="Ticketing")

@app.route('/upcoming')
def upcoming():
    movies = Movie.query.filter_by(is_active=False).all()
    return render_template('upcoming.html.j2', movies=movies, title="即將上映")

#@app.route("/special")
#def special():
    #return render_template("special.html.j2")

@app.route('/cinema')
def cinemas():
    all_cinemas = Cinema.query.all()
    cinema_dict = defaultdict(list)
    for c in all_cinemas:
        cinema_dict[c.region].append(c)
    return render_template('cinema.html.j2', cinema_dict=cinema_dict, title="影院")

@app.route('/cinema/<int:id>')
def cinema_detail(id):
    cinema = Cinema.query.get_or_404(id)
    showtimes = cinema.showtimes.all()
    return render_template('cinema_detail.html.j2', cinema=cinema, showtimes=showtimes, title="影院詳情")

# ====================== 使用者認證路由 ======================
@app.route("/login", methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user or not user.check_password(form.password.data):
            flash('使用者名稱或密碼無效', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    
    return render_template('login.html.j2', form=form, title="登入")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/register", methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('恭喜，您已成功註冊！', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html.j2', form=form, title="註冊")

@app.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html.j2', user=user, title=f"{username} 的個人頁面")

# ====================== 訂票功能路由 ======================
@app.route('/ticket_select/<int:showtime_id>')
def ticket_select(showtime_id):
    showtime = Showtimes.query.get_or_404(showtime_id)
    seats = showtime.hall.seats.all()
    return render_template('seat_select.html.j2', showtime=showtime, seats=seats, title="選擇座位")

@app.route('/book_tickets', methods=['POST'])
def book_tickets():
    if not current_user.is_authenticated:
        return jsonify({"success":False, "message":"請先登入"})
    
    data = request.get_json()
    showtime_id = data.get('showtime_id')
    seat_ids = data.get('seat_ids', [])
    
    if not seat_ids:
        return jsonify({"success":False, "message":"未選擇任何座位"})
    
    total = len(seat_ids) * 80
    
    booking = Booking(
        user_id=current_user.id, 
        showtime_id=showtime_id, 
        total_price=total
    )
    db.session.add(booking)
    db.session.flush()
    
    for s in seat_ids:
        ticket = Tickets(
            booking_id=booking.id, 
            seat_id=s, 
            ticket_code=str(uuid.uuid4())[:8]
        )
        db.session.add(ticket)
        
        seat = Seats.query.get(s)
        if seat:
            seat.is_booked = True
    
    current_user.points -= total
    db.session.commit()
    
    return jsonify({"success":True, "message":"訂票成功！"})

# ====================== 禮品卡 最終新版(符合你要求) ======================
@app.route("/gift_card", methods=["GET", "POST"])
def gift_card():
    error = None

    if request.method == "POST":
        # 1. Check Balance Form
        card_number = request.form.get("card_number")
        pin = request.form.get("pin")

        # 2. Setup Password Form
        setup_card_number = request.form.get("setup_card_number")

        # ---- 查詢餘額邏輯 ----
        if card_number and pin:
            card = GiftCard.query.filter_by(card_number=card_number).first()
            if card and str(card.pin) == pin:
                flash(f"卡號 {card_number} 餘額: HK$ {card.balance:.2f}", "success")
            else:
                error = "無效的禮品卡號或密碼。"

        # ---- 設定密碼 / Top-up 邏輯 (你要的功能) ----
        elif setup_card_number:
            # 必須登入才可設定
            if not current_user.is_authenticated:
                error = "請先登入以設定禮品卡密碼"
            else:
                # 尋找該禮品卡
                card = GiftCard.query.filter_by(card_number=setup_card_number).first()
                if card:
                    # 核心：將 Gift Card Personal Password 改為 使用者ID
                    card.pin = str(current_user.id)
                    db.session.commit()
                    # 你指定的文字
                    flash("Top-up successful", "success")
                else:
                    error = "無效的禮品卡號"

    return render_template("gift_card.html.j2", error=error, title="禮品卡查詢")