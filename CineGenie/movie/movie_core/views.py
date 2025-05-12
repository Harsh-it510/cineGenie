from django.shortcuts import render, redirect
from .forms import RegistrationForm
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from .tmdb_utils import get_popular_movies, get_movie_details, get_top_rated_movies, get_trending_movies, get_popular_tv_shows
from django.http import JsonResponse
from django.conf import settings
from tmdbv3api import TMDb, Movie
import logging
import json
from .aibot import MovieAIBot

logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    # Get different categories of movies from TMDb API
    popular_movies = get_popular_movies(limit=8)
    top_rated_movies = get_top_rated_movies(limit=8)
    trending_movies = get_trending_movies(limit=8)
    popular_tv_shows = get_popular_tv_shows(limit=8)
    
    context = {
        'popular_movies': popular_movies,
        'top_rated_movies': top_rated_movies,
        'trending_movies': trending_movies,
        'popular_tv_shows': popular_tv_shows
    }
    return render(request, 'tmdb_index.html', context)

def signup_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')  # Replace with your actual login URL name
    else:
        form = RegistrationForm()
    return render(request, 'signup.html', {'form': form})

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Authenticate the user
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            # Log the user in
            auth_login(request, user)
            return redirect('index')  # Redirect to homepage after successful login
        else:
            # Return an error message
            return render(request, 'login.html', {'error_message': 'Invalid email or password'})
    
    # If it's a GET request, just render the login page
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('index')

def privacy_policy(request):
    return render(request, 'privacy.html')

def tmdb_test(request):
    # Get popular movies from TMDb API
    popular_movies = get_popular_movies(limit=12)
    
    context = {
        'popular_movies': popular_movies
    }
    return render(request, 'tmdb_test.html', context)

def tmdb_index(request):
    # Get popular movies from TMDb API
    popular_movies = get_popular_movies(limit=8)
    
    context = {
        'popular_movies': popular_movies
    }
    return render(request, 'tmdb_index.html', context)

def debug_tmdb(request):
    """Debug view to directly check TMDb API functionality"""
    try:
        # Initialize TMDb API
        tmdb = TMDb()
        tmdb.api_key = settings.TMDB_API_KEY
        
        # Create movie instance
        movie = Movie()
        
        try:
            # Get popular movies directly with requests
            import requests
            url = f"{settings.TMDB_API_URL}/movie/popular"
            params = {'api_key': settings.TMDB_API_KEY}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                first_movie = data['results'][0] if 'results' in data and data['results'] else None
                
                # Return raw data for debugging
                response_data = {
                    "success": True,
                    "method": "direct_requests",
                    "movie_data": first_movie,
                    "settings": {
                        "api_key_set": bool(settings.TMDB_API_KEY),
                        "image_base_url": settings.TMDB_IMAGE_BASE_URL,
                        "poster_size": settings.TMDB_POSTER_SIZE
                    }
                }
                return JsonResponse(response_data)
            else:
                return JsonResponse({
                    "success": False, 
                    "error": f"API request failed with status code {response.status_code}"
                })
                
        except Exception as req_error:
            # If direct request fails, try the library method but handle object serialization
            popular_movies = movie.popular(page=1)
            
            if popular_movies and len(popular_movies) > 0:
                first_movie = popular_movies[0]
                
                # Convert AsObj to dictionary
                movie_dict = {}
                for attr in dir(first_movie):
                    if not attr.startswith('_') and not callable(getattr(first_movie, attr)):
                        try:
                            value = getattr(first_movie, attr)
                            # Ensure value is JSON serializable
                            if isinstance(value, (str, int, float, bool, list, dict, tuple)) or value is None:
                                movie_dict[attr] = value
                        except Exception as attr_error:
                            movie_dict[attr] = f"Error accessing: {str(attr_error)}"
                
                # Return raw data for debugging
                response_data = {
                    "success": True,
                    "method": "tmdb_library",
                    "movie_data": movie_dict,
                    "settings": {
                        "api_key_set": bool(settings.TMDB_API_KEY),
                        "image_base_url": settings.TMDB_IMAGE_BASE_URL,
                        "poster_size": settings.TMDB_POSTER_SIZE
                    }
                }
                return JsonResponse(response_data)
            else:
                return JsonResponse({
                    "success": False, 
                    "error": "No movies found with TMDb library"
                })
    
    except Exception as e:
        return JsonResponse({
            "success": False, 
            "error": str(e),
            "error_type": str(type(e))
        })
        
def movie_details(request, movie_id=None):
    """
    View function for movie details page.
    If movie_id is provided, show details for that movie.
    """
    if not movie_id and request.GET.get('id'):
        movie_id = request.GET.get('id')
    
    if movie_id:
        movie = get_movie_details(movie_id)
        # Add OTT platform information
        if movie:
            movie_title = movie.get('title', '')
            movie_id = movie.get('id', 0)
            movie['ott_platform'] = get_mock_ott_platform(movie_id, movie_title)
        return render(request, 'details.html', {'movie': movie})
    else:
        # Redirect to home if no movie_id is provided
        return redirect('index')

def search_movies(request):
    """
    Search for movies by title.
    Returns search results as JSON for AJAX requests or renders a search results page.
    """
    query = request.GET.get('query', '')
    
    if not query:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'results': []})
        return render(request, 'search_results.html', {'results': [], 'query': query})
    
    # Use TMDb API to search for movies
    try:
        # Initialize TMDb API with longer timeout
        tmdb = TMDb()
        tmdb.api_key = settings.TMDB_API_KEY
        tmdb.timeout = 30  # Increase timeout
        
        # Create movie instance
        movie = Movie()
        
        # Search for movies
        logger.info(f"Searching for movies with query: {query}")
        search_results = movie.search(query)
        logger.info(f"Found {len(search_results) if search_results else 0} results")
        
        # Process search results
        processed_results = []
        for result in search_results:
            try:
                # Prepare poster path
                poster_path = None
                if hasattr(result, 'poster_path') and result.poster_path:
                    poster_path = f"{settings.TMDB_IMAGE_BASE_URL}{settings.TMDB_POSTER_SIZE}{result.poster_path}"
                
                # Safe attribute access for release year
                release_year = None
                if hasattr(result, 'release_date') and result.release_date:
                    try:
                        release_year = result.release_date[:4]
                    except (IndexError, TypeError):
                        pass
                
                # Get vote average
                vote_average = None
                if hasattr(result, 'vote_average'):
                    vote_average = round(result.vote_average, 1)
                
                # Add mock OTT platform data
                movie_id = result.id if hasattr(result, 'id') else 0
                movie_title = result.title if hasattr(result, 'title') else ""
                ott_platform = get_mock_ott_platform(movie_id, movie_title)
                
                # Build the movie object
                processed_movie = {
                    'id': movie_id,
                    'title': movie_title or "Unknown Title",
                    'poster_path': poster_path,
                    'release_year': release_year,
                    'vote_average': vote_average,
                    'overview': result.overview[:150] + '...' if hasattr(result, 'overview') and result.overview else None,
                    'ott_platform': ott_platform
                }
                processed_results.append(processed_movie)
            except Exception as processing_error:
                logger.error(f"Error processing search result: {str(processing_error)}")
                continue
    
    except Exception as e:
        logger.error(f"Movie search failed: {str(e)}")
        processed_results = []
    
    # Handle AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'results': processed_results})
    
    # Render the search results page for non-AJAX requests
    return render(request, 'search_results.html', {
        'results': processed_results,
        'query': query
    })

def get_mock_ott_platform(movie_id, title):
    """
    Generate mock OTT platform data for demonstration purposes.
    In a production environment, this would be replaced with actual data from a provider API.
    
    Returns a dict with:
    - name: Platform name
    - url: URL to the movie on that platform
    - logo: Path to the platform logo
    """
    # Simple algorithm to assign platforms based on ID or title patterns
    # This is just for demonstration - real data would come from a proper source
    
    # For specific titles (for demonstration)
    title_lower = title.lower()
    if 'panchayat' in title_lower:
        return {
            'name': 'Amazon Prime Video',
            'url': 'https://www.primevideo.com/detail/Panchayat/0KEP4A6DWRKFYQFTSU5RXHEAN2',
            'logo': '/static/images/platforms/prime_video.png'
        }
    
    # Use the movie ID to deterministically assign platforms
    # This ensures the same movie always gets the same platform in our demo
    platform_index = movie_id % 5  # Cycle through 5 possible platforms
    
    platforms = [
        {
            'name': 'Netflix',
            'url': f'https://www.netflix.com/title/{movie_id}',
            'logo': '/static/images/platforms/netflix.png'
        },
        {
            'name': 'Amazon Prime Video',
            'url': f'https://www.primevideo.com/detail/{movie_id}',
            'logo': '/static/images/platforms/prime_video.png'
        },
        {
            'name': 'Disney+ Hotstar',
            'url': f'https://www.hotstar.com/in/movies/{movie_id}',
            'logo': '/static/images/platforms/hotstar.png'
        },
        {
            'name': 'Sony LIV',
            'url': f'https://www.sonyliv.com/movies/{movie_id}',
            'logo': '/static/images/platforms/sonyliv.png'
        },
        {
            'name': 'Zee5',
            'url': f'https://www.zee5.com/movies/{movie_id}',
            'logo': '/static/images/platforms/zee5.png'
        }
    ]
    
    return platforms[platform_index]

def ai_chat(request):
    """
    View function for the AI chat page.
    This allows users to interact with a movie-focused AI chatbot.
    The chatbot can provide movie recommendations, information, and discuss user favorites.
    """
    # Get user favorites from session or empty list
    favorites = request.session.get('favorites', [])
    
    # If user is authenticated, we can load their favorites from database in the future
    # For now, we'll handle this client-side with localStorage
    
    context = {
        'favorites': favorites
    }
    
    return render(request, 'ai_chat.html', context)

def aibot_chat(request):
    """
    View function for handling AI chatbot queries.
    Takes user message and favorite movies as input, returns AI response.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            favorites = data.get('favorites', [])
            
            # Initialize AI bot with API key from settings
            api_key = getattr(settings, 'GEMINI_API_KEY', '')
            bot = MovieAIBot(api_key=api_key)
            
            # Add favorite movies to context if available
            if favorites:
                bot.add_favorite_movies(favorites)
            
            # Get response from AI
            response = bot.get_response(user_message)
            
            return JsonResponse({
                'success': True,
                'step': response.get('step', 'error'),
                'content': response.get('content', 'Sorry, I could not process your request'),
            })
            
        except Exception as e:
            logger.error(f"AI chat error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    # If not a POST request, return error
    return JsonResponse({
        'success': False,
        'error': 'Only POST requests are supported'
    })

def ai_chat_combined(request):
    """
    View function for the combined AI chat page.
    This uses the UI from ai_chat.html with the backend functionality from aibot.
    """
    # Get user favorites from session or empty list
    favorites = request.session.get('favorites', [])
    
    context = {
        'favorites': favorites
    }
    
    return render(request, 'ai_chat_combined.html', context)