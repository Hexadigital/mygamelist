from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from . import views

app_name = 'games'
urlpatterns = [
    path('', views.IndexView, name='index'),
    path('genre/<int:genre_id>/', views.GenreView, name='genre'),
    path('genre/<int:genre_id>/<str:name>/', views.GenreView, name='genre'),
    path('tag/<int:tag_id>/', views.GamesTaggedWithView, name='tag'),
    path('tag/<int:tag_id>/<str:name>/', views.GamesTaggedWithView, name='tag'),
    path('platform/<int:pk>/', views.PlatformView.as_view(), name='platform'),
    path('platform/<int:pk>/<str:name>/', views.PlatformView.as_view(), name='platform'),
    path('game/<int:pk>/', views.GameView.as_view(), name='game'),
    path('game/<int:pk>/<str:name>/', views.GameView.as_view(), name='game'),
    path('user/<int:user_id>/', views.ProfileView, name='profile'),
    path('user/<int:user_id>/<str:name>/', views.ProfileView, name='profile'),
    path('user/<int:user_id>/<str:name>/<str:tab>/', views.ProfileView, name='profile'),
    path('login/', auth_views.LoginView.as_view(template_name='games/login.html'), name='login'),
    path('register/', views.register, name='register'),
    path('gamelist/', views.GameListView, name='gamelist'),
    path('gamelist/<str:edit_type>', views.GameListView, name='gamelist'),
    path('gamelist/<str:edit_type>/<int:entry_id>', views.GameListView, name='gamelist'),
    path('browse/', views.BrowseView, name='browse'),
    path('forums/', views.IndexView, name='forums')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)