from flask import render_template, redirect, flash, url_for, request, jsonify
from collections import defaultdict
from flask_login import current_user, login_user, logout_user
from urllib.parse import urlparse

from app import app, db
from app.models import Cinema
from app.email import send_password_reset_email
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import *

@app.route("/", methods=['GET', 'POST'])
@app.route("/index")
def index():
    return render_template("index.html.j2", title="Home")

#@app.route("/ticketing")
#def ticketing():
    #return render_template("ticketing.html.j2")

#@app.route("/upcoming")
#def upcoming():
    #return render_template("upcoming.html.j2")

#@app.route("/special")
#def special():
    #return render_template("special.html.j2")

#@app.route("/cinema")
#def cinemas_api():
    all_cinemas = Cinema.query.all()
    
    grouped_cinemas = defaultdict(list)
    for cinema in all_cinemas:
        grouped_cinemas[cinema.region].append(cinema)
        
    return render_template('cinema.html.j2', cinemas=grouped_cinemas)
#@app.route('/cinema')
#def cinemas():
    cinema_data = {
        "HK": ["MOVIE MOViE Pacific Place (Admiralty)", "MOVIE MOViE Cityplaza (Taikoo Shing)", "PALACE ifc"],
        "KLN": ["GALA CINEMA (Langham Place)", "PREMIERE ELEMENTS", "B+ cinema MOKO (Mong Kok East)", "B+ cinema apm (Kwun Tong)", "CINEMATHEQUE", "MONGKOK"],
        "NT": ["MY CINEMA YOHO MALL", "KWAI FONG", "TSUEN WAN", "KINGSWOOD"],
        "Macau": ["Studio City Cinema"]
    }
    return render_template('cinema.html.j2', title='Cinema Locations', cinemas=cinema_data)
@app.route('/cinema')
def cinemas():
    # 1. 從資料庫撈出所有電影院
    all_cinemas = Cinema.query.all()
    
    # 2. 將資料按 region 分組
    # 格式會變成: {"HK": [CinemaObj, ...], "KLN": [CinemaObj, ...]}
    cinema_dict = defaultdict(list)
    for c in all_cinemas:
        cinema_dict[c.region].append(c)
        
    return render_template('cinema.html.j2', title='Cinema Locations', cinema_dict=cinema_dict)

@app.route('/cinema/<int:id>')
def cinema_detail(id):
    # 使用 .get_or_404 處理找不到 id 的情況
    cinema = Cinema.query.get_or_404(id)
    return render_template('cinema_detail.html.j2', cinema=cinema)

#@app.route("/gift_card_shop")
#def gift_card_shop():
    #return render_template("gift_card_shop.html.j2")

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


@app.route('/events/<string:slug>')
def event_detail(slug):
    event = Event.query.filter_by(slug=slug).first_or_404()
    return render_template('movie_list.html.j2',
                           movies=event.movies,
                           page_title=event.title,
                           current_filter=None)