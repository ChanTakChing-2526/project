from app import db, app
from app.models import Movie, Event, Cinema, Halls, Seats, Showtimes, User, Booking, Tickets, GiftCard
from datetime import datetime, timedelta, date
from sqlalchemy import text
import random

with app.app_context():
    db.create_all()

    # ====================== 清空舊資料 ======================
    print("正在清空舊資料...")

    # 先刪掉 Tickets 和 Booking
    db.session.query(GiftCard).delete()
    Tickets.query.delete()
    Booking.query.delete()
    db.session.commit()

    # 再刪掉其他表
    db.session.execute(text('DELETE FROM movie_event'))
    db.session.commit()

    Seats.query.delete()
    Showtimes.query.delete()
    Halls.query.delete()
    Cinema.query.delete()
    Event.query.delete()
    Movie.query.delete()
    User.query.delete()
    db.session.commit()


    # ====================== 1. 插入電影 (6 套) ======================
    movies_data = [
        {"moviename": "Cold War 1994", "runtime": 117, "category": "Action", "language": "Cantonese (Chinese,English Subtitle)", "releasedate": date(2026, 5, 1), "poster_url": "https://media.grabticks.com/programxo_8aa13ec4-9b11-4162-aca3-2928bbd1b063__.jpg", "formats": ["IMAX", "4DX", "3D"], "is_active": False},
        {"moviename": "Night King (Director's Cut)", "runtime": 163, "category": "Adult", "language": "Cantonese (Chinese,English Subtitle)", "releasedate": date(2026, 4, 16), "poster_url": "https://media.grabticks.com/programNo_3cf72d03-24af-40e7-a6c2-09649f2a6940__.jpg", "formats": ["IMAX", "4D Blue Ray"], "is_active": True},
        {"moviename": "The Devil Wears Prada 2", "runtime": 120, "category": "Comedy-drama", "language": "English (Chinese Subtitle)", "releasedate": date(2026, 4, 29), "poster_url": "https://media.grabticks.com/programKi_c4e8c9bd-de5f-4cfc-9ee7-d176dacdac8d__.jpg", "formats": ["4DX", "IMAX", "4D Blue Ray"], "is_active": False},
        {"moviename": "COLD WAR", "runtime": 102, "category": "Action", "language": "Cantonese (Chinese,English Subtitle)", "releasedate": date(2026, 4, 16), "poster_url": "https://media.grabticks.com/programEo_d5bce64c-fbca-4a52-b164-c29aebf7fbdd__.jpg", "formats": ["4D Blue Ray", "Dolby Atmos"], "is_active": True},
        {"moviename": "Sirāt", "runtime": 114, "category": "Sci-Fi", "language": "English,Spanish,French,Arabic (Chinese,English Subtitle)", "releasedate": date(2026, 4, 23), "poster_url": "https://media.grabticks.com/programIo_a4e8ce59-bc9a-4a84-b00d-f78532b202c1__.jpg", "formats": ["3D", "Dolby Atmos"], "is_active": True},
        {"moviename": "IMAX Michael", "runtime": 127, "category": "Action", "language": "English (Chinese Subtitle)", "releasedate": date(2026, 4, 22), "poster_url": "https://media.grabticks.com/programUo_8ef97fae-65ce-4c19-9a6b-17aa25a7d7ef__.jpg", "formats": ["IMAX", "4DX"], "is_active": True},
        {"moviename": "Assassination Classroom: Our Future Screening", "runtime": 87, "category": "Animation", "language": "Japanese (Chinese,English Subtitle)", "releasedate": date(2026, 5, 3), "poster_url": "https://media.grabticks.com/programVo_a27a0d23-3024-4a56-ba18-3b53528530c4__.jpg", "formats": ["4D Blue Ray", "Dolby Atmos"], "is_active": False},
    ]

    for data in movies_data:
        movie = Movie(**data)
        db.session.add(movie)
    db.session.commit()
    print("✅ 已插入 6 套電影")

    # ====================== 2. 插入戲院 + 影廳 + 座位 ======================
    cinemas_data = [
        {"cinemaname": "PALACE ifc", "region": "HK", "address": "IFC Mall", "image_url": "https://www.playeahk.com/wp-content/uploads/2023/03/misc_cka_12_1504261261.jpg"},
        {"cinemaname": "MOViE MOViE Pacific Place (Admiralty)", "region": "HK", "address": " Level 1, Pacific Place, 88 Queensway Road, Hong Kong Island", "image_url": "https://images.travelandleisureasia.com/wp-content/uploads/sites/5/2024/04/16152505/hong-kong-movie-tickets-cinema-day-2024.jpeg?tr=w-1366,f-jpg,pr-true"},
        {"cinemaname": "PREMIERE ELEMENTS", "region": "KLN", "address": "2130, 2/F, Fire, ELEMENTS, 1 Austin Road West, Kowloon" , "image_url": "https://www.elementshk.com/v3/assets/blt2e2a6920a8eb4819/blt553399c50459a2e4/5fac1ac6c1502b76a169b96d/Premiere_1360x904.jpg"},
        {"cinemaname": "KWAI FONG", "region": "NT", "address": "L1-L4 Metroplaza, 223 Hing Fong Road, Kwai Fong, NT", "image_url": "https://if.com.au/wp-content/uploads/2020/10/hoyts.jpg"},
        {"cinemaname": "Studio City Cinema", "region": "Macau", "address": "Studio City Level 2, Estrada do Istmo, Cotai, Macau (Escalator from Times Square)" ,"image_url": "https://boniutravel.com/wp-content/uploads/2021/10/1634961871-a522abb8d2a81357c73f38466ff46dfb.jpg"},
    ]

    for c_data in cinemas_data:
        cinema = Cinema(**c_data)
        db.session.add(cinema)
        db.session.flush()

        for i in range(1, 4):
            hall = Halls(cinema_id=cinema.id, hallname=f"Hall {i}")
            db.session.add(hall)
            db.session.flush()

            for row_num in range(1, 9):
                row_code = chr(64 + row_num)  # A ~ H
                for seat_num in range(1, 11):
                    seat = Seats(hall_id=hall.id, row_code=row_code, seat_number=seat_num, is_booked=False)
                    db.session.add(seat)

    db.session.commit()
    print("✅ 已插入戲院、影廳同座位")

    # ====================== 3. 插入活動 ======================
    event1 = Event(title="金像獎特別推介", description="第42屆香港電影金像獎推介電影", start_date=datetime(2025,4,1), end_date=datetime(2025,5,31), banner_image="https://picsum.photos/id/237/800/300")
    event2 = Event(title="4DX 限定場", description="為 4DX 發燒友準備的特別放映", start_date=datetime(2025,4,20), end_date=datetime(2025,5,10), banner_image="https://picsum.photos/id/1015/800/300")

    db.session.add_all([event1, event2])
    db.session.commit()

    # 關聯電影到活動
    all_movies = Movie.query.all()
    for movie in all_movies:
        event1.movies.append(movie)

    movies_4dx = Movie.query.filter(Movie.formats.cast(db.String).ilike("%4DX%")).all()
    for movie in movies_4dx:
        event2.movies.append(movie)

    db.session.commit()
    print("✅ 已插入 2 個活動並關聯電影")

    # ====================== 4. 生成場次 ======================
    active_movies = Movie.query.filter_by(is_active=True).all()
    cinemas = Cinema.query.all()

    for movie in active_movies:
        selected_cinemas = random.sample(cinemas, 2)
        for cinema in selected_cinemas:
            hall = cinema.halls.first()
            for i in range(3):
                start_time = datetime.now() + timedelta(days=random.randint(1,5))
                start_time = start_time.replace(hour=random.randint(10,22), minute=random.choice([0,30]), second=0, microsecond=0)
                end_time = start_time + timedelta(minutes=movie.runtime + 30)

                show = Showtimes(
                    movie_id=movie.id,
                    cinema_id=cinema.id,
                    hall_id=hall.id,
                    start_time=start_time,
                    end_time=end_time,
                    format_type=random.choice(movie.formats) if movie.formats else "2D",
                    price_base=80.0
                )
                db.session.add(show)

    db.session.commit()
    print("✅ 已為上映電影生成場次")

    # ====================== 插入測試用戶 ======================
    for username, points in [("test1000", 1000), ("test500", 500), ("test0", 0)]:
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(
                username=username,
                email=f"{username}@example.com",
                given_name="Test",
                surname="User",
                gender="Male",
                birth_date=datetime(2000, 1, 1),
                about_me="This is a test user",
                last_seen=datetime.utcnow(),
                points=points
            )
            user.set_password("123456")
            db.session.add(user)
        else:
            user.points = points
            user.last_seen = datetime.utcnow()
    db.session.commit()
    print("✅ 已建立測試用戶")

        # ====================== 6. 插入 GiftCard 測試資料 ======================
    print("正在更新 Gift Card 資料...")

    # 先刪除所有舊 Gift Card
    GiftCard.query.delete()
    db.session.commit()

    test_user = User.query.filter_by(username="test1000").first()

    cards = [
        {"card_number": "1234567890123456", "user_id": test_user.id, "balance": 300.0},
        {"card_number": "9876543210987654", "user_id": test_user.id, "balance": 150.0},
        {"card_number": "5555666677778888", "user_id": test_user.id, "balance": 500.0},
    ]

    for c in cards:
        card = GiftCard(
            card_number=c["card_number"],
            user_id=c["user_id"],
            balance=c["balance"],
            is_active=True
        )
        db.session.add(card)

    db.session.commit()
    print("✅ 已建立 3 張新 Gift Card（已連結 User ID）")

    print("\n🎉 所有資料已成功插入！")
    print("你可以開始使用 Ticketing、Upcoming、Events、Cinema、Profile 等功能")

def create_test_users_only():
    """安全版本：只建立測試用戶，唔會刪除現有資料"""
    from app import db, app
    from app.models import User

    with app.app_context():
        test_users = [
            {"username": "test1000", "email": "test1000@example.com", "points": 1000},
            {"username": "test500", "email": "test500@example.com", "points": 500},
            {"username": "test0", "email": "test0@example.com", "points": 0},
        ]
        
        for u in test_users:
            existing = User.query.filter_by(username=u["username"]).first()
            if not existing:
                user = User(
                    username=u["username"],
                    email=u["email"],
                    points=u["points"]
                )
                user.set_password("123456")
                db.session.add(user)
        
        db.session.commit()
        print("✅ 已建立測試用戶（如果未存在）")
