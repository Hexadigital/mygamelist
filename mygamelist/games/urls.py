from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from . import views

app_name = 'games'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('genre/<int:pk>/<str:name>/', views.GenreView.as_view(), name='genre'),
    path('tag/<int:pk>/', views.TagView.as_view(), name='tag'),
    path('tag/<int:pk>/<str:name>/', views.TagView.as_view(), name='tag'),
    path('platform/<int:pk>/', views.PlatformView.as_view(), name='platform'),
    path('platform/<int:pk>/<str:name>/', views.PlatformView.as_view(), name='platform'),
    path('game/<int:pk>/', views.GameView.as_view(), name='game'),
    path('game/<int:pk>/<str:name>/', views.GameView.as_view(), name='game'),
    path('login/', auth_views.LoginView.as_view(template_name='games/login.html'), name='login'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)