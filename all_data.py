
from app import db, app
from app.models import Movie, Event, Cinema, Halls, Seats, Showtimes, User
from datetime import datetime, timedelta, date
from sqlalchemy import text
import random

with app.app_context():
    db.create_all()

    # ====================== 清空舊資料 ======================
    print("正在清空舊資料...")

    db.session.execute(text('DELETE FROM movie_event'))
    db.session.commit()

    Showtimes.query.delete()
    Seats.query.delete()
    Halls.query.delete()
    Cinema.query.delete()
    Event.query.delete()
    Movie.query.delete()
    User.query.delete()
    db.session.commit()

    # ====================== 1. 插入電影 (6 套) ======================
    movies_data = [
        {"moviename": "復仇者聯盟：終局之戰", "runtime": 181, "category": "Action", "language": "粵語", "releasedate": date(2019, 4, 3), "poster_url": "https://picsum.photos/id/1015/300/400", "formats": ["IMAX", "4DX", "3D"], "is_active": True},
        {"moviename": "沙丘：第二部", "runtime": 166, "category": "Sci-Fi", "language": "粵語", "releasedate": date(2024, 4, 1), "poster_url": "https://picsum.photos/id/201/300/400", "formats": ["IMAX", "4D Blue Ray", "Dolby Atmos"], "is_active": True},
        {"moviename": "死侍與金鋼狼", "runtime": 127, "category": "Action", "language": "粵語", "releasedate": date(2024, 5, 27), "poster_url": "https://picsum.photos/id/301/300/400", "formats": ["4DX", "IMAX", "4D Blue Ray"], "is_active": True},
        {"moviename": "腦筋急轉彎2", "runtime": 96, "category": "Animation", "language": "粵語", "releasedate": date(2024, 7, 13), "poster_url": "https://picsum.photos/id/401/300/400", "formats": ["3D", "Dolby Atmos"], "is_active": False},
        {"moviename": "侏羅紀世界：重生", "runtime": 145, "category": "Action", "language": "粵語", "releasedate": date(2025, 1, 22), "poster_url": "https://picsum.photos/id/501/300/400", "formats": ["IMAX", "4DX"], "is_active": False},
        {"moviename": "小丑2:雙重瘋狂", "runtime": 138, "category": "Drama", "language": "粵語", "releasedate": date(2024, 12, 18), "poster_url": "https://picsum.photos/id/601/300/400", "formats": ["4D Blue Ray", "Dolby Atmos"], "is_active": False},
    ]

    for data in movies_data:
        movie = Movie(**data)
        db.session.add(movie)
    db.session.commit()
    print("✅ 已插入 6 套電影")

    # ====================== 2. 插入戲院 + 影廳 + 座位 ======================
    cinemas_data = [
        {"cinemaname": "PALACE ifc", "region": "HK", "address": "IFC Mall", "image_url": "https://www.playeahk.com/wp-content/uploads/2023/03/misc_cka_12_1504261261.jpg"},
        {"cinemaname": "MOVIE MOVIE Cityplaza", "region": "HK", "address": "Cityplaza"},
        {"cinemaname": "PREMIERE ELEMENTS", "region": "KLN", "address": "Elements"},
        {"cinemaname": "MY CINEMA YOHO MALL", "region": "NT", "address": "Yoho Mall"},
        {"cinemaname": "The Grand Cinema", "region": "KLN", "address": "旺角"},
    ]

    for c_data in cinemas_data:
        cinema = Cinema(**c_data)
        db.session.add(cinema)
        db.session.flush()

        # 每間戲院建立 3 個影廳
        for i in range(1, 4):
            hall = Halls(cinema_id=cinema.id, hallname=f"Hall {i}")
            db.session.add(hall)
            db.session.flush()

            # 每個影廳生成 8 排 × 10 個座位
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

    # ====================== 5. 插入測試用戶 ======================
    for username, points in [("test1000", 1000), ("test500", 500), ("test0", 0)]:
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, email=f"{username}@example.com")
            user.set_password("123456")
            user.points = points
            db.session.add(user)
        else:
            user.points = points
    db.session.commit()
    print("✅ 已建立測試用戶")

    print("\n🎉 所有資料已成功插入！")
    print("你可以開始使用 Ticketing、Upcoming、Events、Cinema、Profile 等功能")
