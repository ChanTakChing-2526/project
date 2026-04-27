from flask import Blueprint, render_template
from app.models import Movie

movies_bp = Blueprint('movies', __name__, url_prefix='/movies')

@movies_bp.route('/')
def movie_list():
    movies = Movie.query.filter_by(is_active=True).all()
    return render_template('movie_list.html.j2', show_secondary_navbar=True, movies=movies, page_title="Now Showing", current_filter=None)

@movies_bp.route('/<string:format_filter>')
def movies_by_format(format_filter):
    format_filter = format_filter.lower().strip().replace('-', ' ')
    
    all_movies = Movie.query.filter_by(is_active=True).all()
    filtered_movies = []
    for movie in all_movies:
        if movie.formats and any(format_filter in f.lower() for f in movie.formats):
            filtered_movies.append(movie)
    
    print(f"🔍 [Blueprint] Filter '{format_filter}' → Found {len(filtered_movies)} movies")
    
    return render_template('movie_list.html.j2', show_secondary_navbar=True, movies=filtered_movies, page_title=f"{format_filter.upper()} Movies", current_filter=format_filter)