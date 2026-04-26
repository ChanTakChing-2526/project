from app import app, db
from app.models import Cinema

data = [
    {"cinemaname": "PALACE ifc", "region": "HK", "address": "IFC Mall"},
    {"cinemaname": "MOVIE MOViE Cityplaza", "region": "HK", "address": "Cityplaza"},
    {"cinemaname": "PREMIERE ELEMENTS", "region": "KLN", "address": "Elements"},
    {"cinemaname": "MY CINEMA YOHO MALL", "region": "NT", "address": "Yoho Mall"}
]

with app.app_context():
    # --- 關鍵修改：這行會自動幫你建立所有定義在 models.py 的表格 ---
    db.create_all() 
    print("資料表已確保建立。")
    
    for d in data:
        exists = Cinema.query.filter_by(cinemaname=d['cinemaname']).first()
        if not exists:
            new_cinema = Cinema(cinemaname=d['cinemaname'], region=d['region'], address=d['address'])
            db.session.add(new_cinema)
            print(f"新增: {d['cinemaname']}")
        else:
            print(f"已存在，跳過: {d['cinemaname']}")
    
    db.session.commit()
    print("資料同步完成！")