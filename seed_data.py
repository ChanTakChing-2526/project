from app import app, db
from app.models import Cinema

# 定義要新增的資料清單
data = [
    {"cinemaname": "PALACE ifc", "region": "HK", "address": "IFC Mall"},
    {"cinemaname": "MOVIE MOViE Cityplaza", "region": "HK", "address": "Cityplaza"},
    {"cinemaname": "PREMIERE ELEMENTS", "region": "KLN", "address": "Elements"},
    {"cinemaname": "MY CINEMA YOHO MALL", "region": "NT", "address": "Yoho Mall"}
]

with app.app_context():
    # 轉換為 Cinema 物件列表
    cinemas = [Cinema(cinemaname=d['cinemaname'], region=d['region'], address=d['address']) for d in data]
    
    # 一次寫入
    db.session.add_all(cinemas)
    db.session.commit()
    print("資料匯入成功！")