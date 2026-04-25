from flask import Blueprint, render_template
from app.models import Movie

# 建立 Blueprint
movies_bp = Blueprint('movies', __name__, url_prefix='/movies')

# ======================
# 1. Ticketing 主頁 - 只顯示正在上映電影
# ======================
@movies_bp.route('/')
def movie_list():
    # 只顯示 is_active=True 嘅電影
    movies = Movie.query.filter_by(is_active=True).all()
    return render_template('movie_list.html.j2',
                           movies=movies,
                           page_title="現正上映",
                           current_filter=None)

# ======================
# 2. 動態格式篩選 - 只顯示正在上映 + 符合格式
# ======================
@movies_bp.route('/<string:format_filter>')
def movies_by_format(format_filter):
    format_filter = format_filter.lower().strip().replace('-', ' ')
    
    # 只顯示正在上映 + 符合格式
    all_movies = Movie.query.filter_by(is_active=True).all()
    filtered_movies = []
    for movie in all_movies:
        if movie.formats and any(format_filter in f.lower() for f in movie.formats):
            filtered_movies.append(movie)
    
    print(f"🔍 [Blueprint] 篩選 '{format_filter}' → 找到 {len(filtered_movies)} 套上映電影")
    
    return render_template('movie_list.html.j2',
                           movies=filtered_movies,
                           page_title=f"{format_filter.upper()} 電影",
                           current_filter=format_filter)