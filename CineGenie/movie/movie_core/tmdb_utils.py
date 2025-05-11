from django.conf import settings
from tmdbv3api import TMDb, Movie, Genre, TV, Trending
import logging
import requests
import json
import time
import socket
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Create a session with retry logic
def create_requests_session(retries=3, backoff_factor=0.3):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(500, 502, 503, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def init_tmdb():
    """Initialize TMDb API client"""
    tmdb = TMDb()
    tmdb.api_key = settings.TMDB_API_KEY
    # Set a longer timeout
    tmdb.timeout = 10
    return tmdb

def fetch_direct_with_requests(endpoint, params=None):
    """Fetch data directly using requests as a fallback method"""
    if params is None:
        params = {}
    
    params['api_key'] = settings.TMDB_API_KEY
    
    url = f"{settings.TMDB_API_URL}/{endpoint}"
    
    # Use session with retry logic
    session = create_requests_session()
    
    try:
        # Use a longer timeout
        response = session.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except (requests.RequestException, socket.error) as e:
        logger.error(f"Connection error when fetching {endpoint}: {str(e)}")
        return None

def get_popular_movies(page=1, limit=8):
    """Get popular movies from TMDb API"""
    # We'll use the direct request approach first for reliability
    movies_data = fetch_direct_with_requests("movie/popular", {"page": page})
    
    if movies_data and 'results' in movies_data and movies_data['results']:
        # Get genres for mapping
        all_genres = {}
        genres_data = fetch_direct_with_requests("genre/movie/list")
        if genres_data and 'genres' in genres_data:
            all_genres = {genre['id']: genre['name'] for genre in genres_data['genres']}
        
        # Process the results
        processed_movies = []
        results = movies_data['results'][:limit] if limit else movies_data['results']
        
        for movie in results:
            # Extract genres
            genres = []
            if 'genre_ids' in movie and movie['genre_ids']:
                for genre_id in movie['genre_ids']:
                    if genre_id in all_genres:
                        genres.append(all_genres[genre_id])
                        if len(genres) >= 1:  # Only get the first genre
                            break
            
            # Safe attribute access
            release_year = None
            if 'release_date' in movie and movie['release_date']:
                try:
                    release_year = movie['release_date'][:4]
                except (IndexError, TypeError):
                    pass
            
            # Prepare poster path
            poster_path = None
            if 'poster_path' in movie and movie['poster_path']:
                poster_path = f"{settings.TMDB_IMAGE_BASE_URL}{settings.TMDB_POSTER_SIZE}{movie['poster_path']}"
            
            # Build the movie object
            processed_movie = {
                'id': movie.get('id'),
                'title': movie.get('title', "Unknown Title"),
                'poster_path': poster_path,
                'release_year': release_year,
                'vote_average': round(movie.get('vote_average', 0), 1),
                'genres': genres
            }
            processed_movies.append(processed_movie)
        
        return processed_movies
    
    # If direct request fails, try the TMDb library approach
    try:
        logger.info("Direct request failed, trying TMDb library")
        # Initialize TMDb API with longer timeout
        tmdb = TMDb()
        tmdb.api_key = settings.TMDB_API_KEY
        tmdb.timeout = 15  # Set a longer timeout
        
        # Create movie instance
        movie = Movie()
        
        # Get popular movies
        popular_movies = movie.popular(page=page)
        
        # Limit the number of results if needed
        if limit:
            popular_movies = popular_movies[:limit]
        
        # Try to get genres - handle exceptions separately to avoid failing the whole function
        all_genres = {}
        try:
            genre_obj = Genre()
            all_genres = {genre.id: genre.name for genre in genre_obj.movie_list()}
        except Exception as genre_error:
            logger.warning(f"Failed to fetch genres: {str(genre_error)}")
        
        # Process movie data
        processed_movies = []
        for movie_data in popular_movies:
            # Extract genres
            genres = []
            if hasattr(movie_data, 'genre_ids') and movie_data.genre_ids:
                for genre_id in movie_data.genre_ids:
                    if genre_id in all_genres:
                        genres.append(all_genres[genre_id])
                        if len(genres) >= 1:  # Only get the first genre
                            break
            
            # Safe attribute access
            release_year = None
            if hasattr(movie_data, 'release_date') and movie_data.release_date:
                try:
                    release_year = movie_data.release_date[:4]
                except (IndexError, TypeError):
                    pass
            
            # Prepare poster path
            poster_path = None
            if hasattr(movie_data, 'poster_path') and movie_data.poster_path:
                poster_path = f"{settings.TMDB_IMAGE_BASE_URL}{settings.TMDB_POSTER_SIZE}{movie_data.poster_path}"
            
            # Build the movie object
            processed_movie = {
                'id': movie_data.id if hasattr(movie_data, 'id') else None,
                'title': movie_data.title if hasattr(movie_data, 'title') else "Unknown Title",
                'poster_path': poster_path,
                'release_year': release_year,
                'vote_average': round(movie_data.vote_average, 1) if hasattr(movie_data, 'vote_average') else None,
                'genres': genres
            }
            processed_movies.append(processed_movie)
        
        return processed_movies
        
    except Exception as e:
        logger.error(f"Both direct and library approaches failed: {str(e)}")
        # Create some placeholder data
        placeholder_movies = [
            {
                'id': 1,
                'title': "API Connection Issue",
                'poster_path': None,
                'release_year': None,
                'vote_average': None,
                'genres': ["Error"]
            }
        ]
        return placeholder_movies

def get_top_rated_movies(page=1, limit=8):
    """Get top rated movies from TMDb API"""
    # Direct request approach
    movies_data = fetch_direct_with_requests("movie/top_rated", {"page": page})
    
    if movies_data and 'results' in movies_data and movies_data['results']:
        # Get genres for mapping
        all_genres = {}
        genres_data = fetch_direct_with_requests("genre/movie/list")
        if genres_data and 'genres' in genres_data:
            all_genres = {genre['id']: genre['name'] for genre in genres_data['genres']}
        
        # Process the results
        processed_movies = []
        results = movies_data['results'][:limit] if limit else movies_data['results']
        
        for movie in results:
            # Extract genres
            genres = []
            if 'genre_ids' in movie and movie['genre_ids']:
                for genre_id in movie['genre_ids']:
                    if genre_id in all_genres:
                        genres.append(all_genres[genre_id])
                        if len(genres) >= 1:  # Only get the first genre
                            break
            
            # Safe attribute access
            release_year = None
            if 'release_date' in movie and movie['release_date']:
                try:
                    release_year = movie['release_date'][:4]
                except (IndexError, TypeError):
                    pass
            
            # Prepare poster path
            poster_path = None
            if 'poster_path' in movie and movie['poster_path']:
                poster_path = f"{settings.TMDB_IMAGE_BASE_URL}{settings.TMDB_POSTER_SIZE}{movie['poster_path']}"
            
            # Build the movie object
            processed_movie = {
                'id': movie.get('id'),
                'title': movie.get('title', "Unknown Title"),
                'poster_path': poster_path,
                'release_year': release_year,
                'vote_average': round(movie.get('vote_average', 0), 1),
                'genres': genres
            }
            processed_movies.append(processed_movie)
        
        return processed_movies
    
    # If direct request fails, try the TMDb library approach
    try:
        # Initialize TMDb API
        tmdb = TMDb()
        tmdb.api_key = settings.TMDB_API_KEY
        tmdb.timeout = 15
        
        # Create movie instance
        movie = Movie()
        
        # Get top rated movies
        top_rated_movies = movie.top_rated(page=page)
        
        # Limit the number of results if needed
        if limit:
            top_rated_movies = top_rated_movies[:limit]
        
        # Process data as in the get_popular_movies function
        all_genres = {}
        try:
            genre_obj = Genre()
            all_genres = {genre.id: genre.name for genre in genre_obj.movie_list()}
        except Exception as genre_error:
            logger.warning(f"Failed to fetch genres: {str(genre_error)}")
        
        processed_movies = []
        for movie_data in top_rated_movies:
            genres = []
            if hasattr(movie_data, 'genre_ids') and movie_data.genre_ids:
                for genre_id in movie_data.genre_ids:
                    if genre_id in all_genres:
                        genres.append(all_genres[genre_id])
                        if len(genres) >= 1:
                            break
            
            release_year = None
            if hasattr(movie_data, 'release_date') and movie_data.release_date:
                try:
                    release_year = movie_data.release_date[:4]
                except (IndexError, TypeError):
                    pass
            
            poster_path = None
            if hasattr(movie_data, 'poster_path') and movie_data.poster_path:
                poster_path = f"{settings.TMDB_IMAGE_BASE_URL}{settings.TMDB_POSTER_SIZE}{movie_data.poster_path}"
            
            processed_movie = {
                'id': movie_data.id if hasattr(movie_data, 'id') else None,
                'title': movie_data.title if hasattr(movie_data, 'title') else "Unknown Title",
                'poster_path': poster_path,
                'release_year': release_year,
                'vote_average': round(movie_data.vote_average, 1) if hasattr(movie_data, 'vote_average') else None,
                'genres': genres
            }
            processed_movies.append(processed_movie)
        
        return processed_movies
        
    except Exception as e:
        logger.error(f"Both direct and library approaches failed for top rated movies: {str(e)}")
        # Return placeholder data
        return [{'id': 1, 'title': "API Connection Issue", 'poster_path': None, 'release_year': None, 'vote_average': None, 'genres': ["Error"]}]

def get_trending_movies(time_window="week", page=1, limit=8):
    """Get trending movies from TMDb API
    time_window: 'day' or 'week'
    """
    # Direct request approach
    endpoint = f"trending/movie/{time_window}"
    movies_data = fetch_direct_with_requests(endpoint, {"page": page})
    
    if movies_data and 'results' in movies_data and movies_data['results']:
        # Get genres for mapping
        all_genres = {}
        genres_data = fetch_direct_with_requests("genre/movie/list")
        if genres_data and 'genres' in genres_data:
            all_genres = {genre['id']: genre['name'] for genre in genres_data['genres']}
        
        # Process the results
        processed_movies = []
        results = movies_data['results'][:limit] if limit else movies_data['results']
        
        for movie in results:
            # Extract genres
            genres = []
            if 'genre_ids' in movie and movie['genre_ids']:
                for genre_id in movie['genre_ids']:
                    if genre_id in all_genres:
                        genres.append(all_genres[genre_id])
                        if len(genres) >= 1:  # Only get the first genre
                            break
            
            # Safe attribute access
            release_year = None
            if 'release_date' in movie and movie['release_date']:
                try:
                    release_year = movie['release_date'][:4]
                except (IndexError, TypeError):
                    pass
            
            # Prepare poster path
            poster_path = None
            if 'poster_path' in movie and movie['poster_path']:
                poster_path = f"{settings.TMDB_IMAGE_BASE_URL}{settings.TMDB_POSTER_SIZE}{movie['poster_path']}"
            
            # Build the movie object
            processed_movie = {
                'id': movie.get('id'),
                'title': movie.get('title', "Unknown Title"),
                'poster_path': poster_path,
                'release_year': release_year,
                'vote_average': round(movie.get('vote_average', 0), 1),
                'genres': genres
            }
            processed_movies.append(processed_movie)
        
        return processed_movies
    
    # If direct request fails, try the TMDb library approach
    try:
        # Initialize TMDb API
        tmdb = TMDb()
        tmdb.api_key = settings.TMDB_API_KEY
        tmdb.timeout = 15
        
        # Create trending instance
        trending = Trending()
        
        # Get trending movies
        trending_movies = trending.movie_week() if time_window == "week" else trending.movie_day()
        
        # Limit the number of results if needed
        if limit:
            trending_movies = trending_movies[:limit]
        
        # Process data as in the get_popular_movies function
        all_genres = {}
        try:
            genre_obj = Genre()
            all_genres = {genre.id: genre.name for genre in genre_obj.movie_list()}
        except Exception as genre_error:
            logger.warning(f"Failed to fetch genres: {str(genre_error)}")
        
        processed_movies = []
        for movie_data in trending_movies:
            genres = []
            if hasattr(movie_data, 'genre_ids') and movie_data.genre_ids:
                for genre_id in movie_data.genre_ids:
                    if genre_id in all_genres:
                        genres.append(all_genres[genre_id])
                        if len(genres) >= 1:
                            break
            
            release_year = None
            if hasattr(movie_data, 'release_date') and movie_data.release_date:
                try:
                    release_year = movie_data.release_date[:4]
                except (IndexError, TypeError):
                    pass
            
            poster_path = None
            if hasattr(movie_data, 'poster_path') and movie_data.poster_path:
                poster_path = f"{settings.TMDB_IMAGE_BASE_URL}{settings.TMDB_POSTER_SIZE}{movie_data.poster_path}"
            
            processed_movie = {
                'id': movie_data.id if hasattr(movie_data, 'id') else None,
                'title': movie_data.title if hasattr(movie_data, 'title') else "Unknown Title",
                'poster_path': poster_path,
                'release_year': release_year,
                'vote_average': round(movie_data.vote_average, 1) if hasattr(movie_data, 'vote_average') else None,
                'genres': genres
            }
            processed_movies.append(processed_movie)
        
        return processed_movies
        
    except Exception as e:
        logger.error(f"Both direct and library approaches failed for trending movies: {str(e)}")
        # Return placeholder data
        return [{'id': 1, 'title': "API Connection Issue", 'poster_path': None, 'release_year': None, 'vote_average': None, 'genres': ["Error"]}]

def get_popular_tv_shows(page=1, limit=8):
    """Get popular TV shows from TMDb API"""
    # Direct request approach
    tv_data = fetch_direct_with_requests("tv/popular", {"page": page})
    
    if tv_data and 'results' in tv_data and tv_data['results']:
        # Get genres for mapping
        all_genres = {}
        genres_data = fetch_direct_with_requests("genre/tv/list")
        if genres_data and 'genres' in genres_data:
            all_genres = {genre['id']: genre['name'] for genre in genres_data['genres']}
        
        # Process the results
        processed_shows = []
        results = tv_data['results'][:limit] if limit else tv_data['results']
        
        for show in results:
            # Extract genres
            genres = []
            if 'genre_ids' in show and show['genre_ids']:
                for genre_id in show['genre_ids']:
                    if genre_id in all_genres:
                        genres.append(all_genres[genre_id])
                        if len(genres) >= 1:  # Only get the first genre
                            break
            
            # Safe attribute access
            first_air_year = None
            if 'first_air_date' in show and show['first_air_date']:
                try:
                    first_air_year = show['first_air_date'][:4]
                except (IndexError, TypeError):
                    pass
            
            # Prepare poster path
            poster_path = None
            if 'poster_path' in show and show['poster_path']:
                poster_path = f"{settings.TMDB_IMAGE_BASE_URL}{settings.TMDB_POSTER_SIZE}{show['poster_path']}"
            
            # Build the TV show object
            processed_show = {
                'id': show.get('id'),
                'title': show.get('name', "Unknown Title"),
                'poster_path': poster_path,
                'release_year': first_air_year,
                'vote_average': round(show.get('vote_average', 0), 1),
                'genres': genres
            }
            processed_shows.append(processed_show)
        
        return processed_shows
    
    # If direct request fails, try the TMDb library approach
    try:
        # Initialize TMDb API
        tmdb = TMDb()
        tmdb.api_key = settings.TMDB_API_KEY
        tmdb.timeout = 15
        
        # Create TV instance
        tv = TV()
        
        # Get popular TV shows
        popular_shows = tv.popular(page=page)
        
        # Limit the number of results if needed
        if limit:
            popular_shows = popular_shows[:limit]
        
        # Process data
        all_genres = {}
        try:
            genre_obj = Genre()
            all_genres = {genre.id: genre.name for genre in genre_obj.tv_list()}
        except Exception as genre_error:
            logger.warning(f"Failed to fetch TV genres: {str(genre_error)}")
        
        processed_shows = []
        for show_data in popular_shows:
            genres = []
            if hasattr(show_data, 'genre_ids') and show_data.genre_ids:
                for genre_id in show_data.genre_ids:
                    if genre_id in all_genres:
                        genres.append(all_genres[genre_id])
                        if len(genres) >= 1:
                            break
            
            first_air_year = None
            if hasattr(show_data, 'first_air_date') and show_data.first_air_date:
                try:
                    first_air_year = show_data.first_air_date[:4]
                except (IndexError, TypeError):
                    pass
            
            poster_path = None
            if hasattr(show_data, 'poster_path') and show_data.poster_path:
                poster_path = f"{settings.TMDB_IMAGE_BASE_URL}{settings.TMDB_POSTER_SIZE}{show_data.poster_path}"
            
            processed_show = {
                'id': show_data.id if hasattr(show_data, 'id') else None,
                'title': show_data.name if hasattr(show_data, 'name') else "Unknown Title",
                'poster_path': poster_path,
                'release_year': first_air_year,
                'vote_average': round(show_data.vote_average, 1) if hasattr(show_data, 'vote_average') else None,
                'genres': genres
            }
            processed_shows.append(processed_show)
        
        return processed_shows
        
    except Exception as e:
        logger.error(f"Both direct and library approaches failed for TV shows: {str(e)}")
        # Return placeholder data
        return [{'id': 1, 'title': "API Connection Issue", 'poster_path': None, 'release_year': None, 'vote_average': None, 'genres': ["Error"]}]

def get_movie_details(movie_id):
    """Get detailed information for a specific movie"""
    # Try direct request first for reliability
    movie_data = fetch_direct_with_requests(f"movie/{movie_id}")
    
    if movie_data:
        # Extract genre names
        genres = []
        if 'genres' in movie_data and movie_data['genres']:
            for genre in movie_data['genres'][:2]:  # Get up to 2 genres
                if isinstance(genre, dict) and 'name' in genre:
                    genres.append(genre['name'])
        
        # Safe attribute access
        release_year = None
        if 'release_date' in movie_data and movie_data['release_date']:
            try:
                release_year = movie_data['release_date'][:4]
            except (IndexError, TypeError):
                pass
        
        # Prepare poster path
        poster_path = None
        if 'poster_path' in movie_data and movie_data['poster_path']:
            poster_path = f"{settings.TMDB_IMAGE_BASE_URL}{settings.TMDB_POSTER_SIZE}{movie_data['poster_path']}"
        
        # Prepare backdrop path
        backdrop_path = None
        if 'backdrop_path' in movie_data and movie_data['backdrop_path']:
            backdrop_path = f"{settings.TMDB_IMAGE_BASE_URL}original{movie_data['backdrop_path']}"
        
        return {
            'id': movie_data.get('id'),
            'title': movie_data.get('title', "Unknown Title"),
            'poster_path': poster_path,
            'backdrop_path': backdrop_path,
            'release_year': release_year,
            'vote_average': round(movie_data.get('vote_average', 0), 1),
            'genres': genres,
            'overview': movie_data.get('overview'),
            'runtime': movie_data.get('runtime')
        }
        
    # If direct request fails, try the library approach
    try:
        # Initialize TMDb API with longer timeout
        tmdb = TMDb()
        tmdb.api_key = settings.TMDB_API_KEY
        tmdb.timeout = 15  # Set a longer timeout
        
        # Create movie instance
        movie = Movie()
        
        # Get movie details
        movie_details = movie.details(movie_id)
        
        # Extract genre names
        genres = []
        if hasattr(movie_details, 'genres'):
            for genre in movie_details.genres[:2]:  # Get up to 2 genres
                if isinstance(genre, dict) and 'name' in genre:
                    genres.append(genre['name'])
        
        # Safe attribute access
        release_year = None
        if hasattr(movie_details, 'release_date') and movie_details.release_date:
            try:
                release_year = movie_details.release_date[:4]
            except (IndexError, TypeError):
                pass
        
        # Prepare poster path
        poster_path = None
        if hasattr(movie_details, 'poster_path') and movie_details.poster_path:
            poster_path = f"{settings.TMDB_IMAGE_BASE_URL}{settings.TMDB_POSTER_SIZE}{movie_details.poster_path}"
        
        # Prepare backdrop path
        backdrop_path = None
        if hasattr(movie_details, 'backdrop_path') and movie_details.backdrop_path:
            backdrop_path = f"{settings.TMDB_IMAGE_BASE_URL}original{movie_details.backdrop_path}"
        
        return {
            'id': movie_details.id if hasattr(movie_details, 'id') else None,
            'title': movie_details.title if hasattr(movie_details, 'title') else "Unknown Title",
            'poster_path': poster_path,
            'backdrop_path': backdrop_path,
            'release_year': release_year,
            'vote_average': round(movie_details.vote_average, 1) if hasattr(movie_details, 'vote_average') else None,
            'genres': genres,
            'overview': movie_details.overview if hasattr(movie_details, 'overview') else None,
            'runtime': movie_details.runtime if hasattr(movie_details, 'runtime') else None
        }
    
    except Exception as e:
        logger.error(f"Both direct and library approaches failed for movie details: {str(e)}")
        # Return a placeholder movie
        return {
            'id': movie_id,
            'title': "API Connection Issue",
            'poster_path': None,
            'backdrop_path': None,
            'release_year': None,
            'vote_average': None,
            'genres': ["Error"],
            'overview': "Unable to fetch movie details due to API connection issues.",
            'runtime': None
        } 