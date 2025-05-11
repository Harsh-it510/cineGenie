from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('signin/', views.login, name="login"),
    path('signup/', views.signup_view, name="signup"),
    path('logout/', views.logout_view, name="logout"),
    path('privacy/', views.privacy_policy, name="privacy"),
    path('tmdb-test/', views.tmdb_test, name="tmdb_test"),
    path('tmdb-index/', views.tmdb_index, name="tmdb_index"),
    path('debug-tmdb/', views.debug_tmdb, name="debug_tmdb"),
    path('movie/<int:movie_id>/', views.movie_details, name="movie_details_with_id"),
    path('movie/', views.movie_details, name="movie_details"),
    path('search/', views.search_movies, name="search_movies"),
    path('ai-chat/', views.ai_chat, name="ai_chat"),
]