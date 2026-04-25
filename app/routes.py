from flask import render_template, redirect, flash, url_for, request, jsonify
from collections import defaultdict
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
from sqlalchemy import asc

from app import app, db
from app.models import Movie, Cinema, Showtimes, Seats, Booking, Tickets
from sqlalchemy.orm import selectinload
from app.email import send_password_reset_email
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm, BookingForm
from app.models import *


@app.route("/", methods=['GET', 'POST'])
@app.route("/index")
def index():
    return render_template("index.html.j2", title="Home")

@app.route("/ticketing")
def ticketing():
    # 這裡抓取「所有」上映中的電影
    # 建議加入 filter，例如只抓 is_active=True 的電影
    #all_movies = Movie.query.filter_by(is_active=True).all()
    #all_movies = Movie.query.options(selectinload(Movie.showtimes)).filter_by(is_active=True).all()
    
    #return render_template("ticketing.html.j2", movies=all_movies)
    
    # 注意：這裡直接傳 movies=all_movies，而不是 movies_dict
    # 這樣你的模板 {% for movie in movies %} 就能直接跑迴圈
    #return render_template("movie_list.html.j2", movies=all_movies, page_title="上映中", current_filter="全部電影")
    # 1. 撈出所有電影
    all_movies = Movie.query.options(selectinload(Movie.showtimes)).filter_by(is_active=True).all()
    
    # 2. 【關鍵步驟】手動幫每個 movie 物件加上 .grouped_showtimes 屬性
    for movie in all_movies:
        # 建立一個暫存用的字典
        grouped = defaultdict(list)
        
        # 將 showtimes 依照地區分組
        for show in movie.showtimes:
            # 確保 cinema 物件存在才取值，避免報錯
            region = show.cinema.region if show.cinema else "未知地區"
            grouped[region].append(show)
            
        # 把算好的資料「掛」到 movie 物件上，變成該物件的屬性
        movie.grouped_showtimes = dict(grouped)
    
    # 3. 再把裝載好的 movies 傳給模板
    return render_template("ticketing.html.j2", movies=all_movies)

@app.route("/upcoming")
def upcoming():
    return render_template("upcoming.html.j2")

@app.route("/special")
def special():
    return render_template("special.html.j2")

@app.route('/cinema')
def cinemas():
    # 1. 從資料庫撈出所有電影院
    all_cinemas = Cinema.query.all()
    
    # 2. 將資料按 region 分組
    cinema_dict = defaultdict(list)
    for c in all_cinemas:
        cinema_dict[c.region].append(c)
        
    return render_template('cinema.html.j2', title='Cinema Locations', cinema_dict=cinema_dict)

@app.route('/cinema/<int:id>')
def cinema_detail(id):
    # 使用 .get_or_404 處理找不到 id 的情況
    cinema = Cinema.query.get_or_404(id)
    showtimes = cinema.showtimes.order_by(Showtimes.movie_id, Showtimes.start_time).all()
    return render_template('cinema_detail.html.j2', cinema=cinema)

#@app.route("/gift_card_shop")
#def gift_card_shop():
    #return render_template("gift_card_shop.html.j2")
#/<int:showtime_id>
@app.route('/booking/<int:showtime_id>', methods=['GET', 'POST'])
@login_required
def booking(showtime_id):
    form = BookingForm()
    
    # 1. 執行查詢 (只執行一次)
    showtime = Showtimes.query.get_or_404(showtime_id)
    all_seats = Seats.query.filter_by(hall_id=showtime.hall_id).all()
    booked_tickets = Tickets.query.join(Booking).filter(Booking.showtime_id == showtime_id).all()
    booked_seat_ids = [ticket.seat_id for ticket in booked_tickets]

    # 2. 處理表單送出 (POST 請求)
    if form.validate_on_submit():
        seat_data = form.selected_seats.data
        # 這裡建議加一個檢查，確保 seat_data 不是空的
        if seat_data:
            seat_id_list = [int(s) for s in seat_data.split(',')]
            
            # --- 在這裡補上你的建立 Booking 與 Tickets 的資料庫邏輯 ---
            # ...
            
            flash("訂票成功！")
            return redirect(url_for('index')) # 或導向訂單確認頁面

    # 3. 渲染頁面 (GET 請求或是表單驗證失敗時)
    return render_template('booking.html.j2', form=form, showtime=showtime, all_seats=all_seats, booked_seat_ids=booked_seat_ids) # 記得傳入這個變數給前端畫座位圖

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
        redirect(next_page)
    return render_template('login.html.j2', title="Sign In", form=form)

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
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congraduations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html.j2', title="Register", form=form)

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
    return render_template('reset_password_request.html.j2', title="Reset Password", form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
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
    return render_template('reset_password.html.j2', title="Reset Password", form=form)

@app.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    posts = user.followed_posts().paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for(
        'index', page=posts.next_num) if posts.next_num else None
    prev_url = url_for(
        'index', page=posts.prev_num) if posts.prev_num else None
    return render_template('user.html.j2', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


# ====================== 活動功能 ======================
@app.route('/events')
def events_list():
    events = Event.query.order_by(Event.start_date.desc()).all()
    return render_template('events_list.html.j2', events=events)


#@app.route('/events/<string:slug>')
#def event_detail(slug):
    event = Event.query.filter_by(slug=slug).first_or_404()
    return render_template('movie_list.html.j2',
                           movies=event.movies,
                           page_title=event.title,
                           current_filter=None)
@app.route('/events/<string:slug>')
def event_detail(slug):
    # 這裡抓取「特定活動」
    event = Event.query.filter_by(slug=slug).first_or_404()
    
    # 這裡只傳該活動關聯的 movies，模板會自動顯示這些電影
    return render_template('movie_list.html.j2',
                           movies=event.movies,
                           page_title=event.title,
                           current_filter="影展專題")