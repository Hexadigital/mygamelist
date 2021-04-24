from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import generic

from .models import Game, Genre, Platform, Tag

class IndexView(generic.ListView):
    template_name = 'games/index.html'
    context_object_name = 'latest_games'

    def get_queryset(self):
        return Game.objects.order_by('name')

class TagView(generic.DetailView):
    model = Tag

class GenreView(generic.DetailView):
    model = Genre

class PlatformView(generic.DetailView):
    model = Platform

class GameView(generic.DetailView):
    model = Game