from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib.auth import login, authenticate

from .models import Game, Genre, Platform, Tag
from .forms import SignUpForm

class IndexView(generic.ListView):
    template_name = 'games/index.html'
    context_object_name = 'latest_games'

    def get_queryset(self):
        return Game.objects.order_by('-id')[:25]

class TagView(generic.DetailView):
    model = Tag

class GenreView(generic.DetailView):
    model = Genre

class PlatformView(generic.DetailView):
    model = Platform

class GameView(generic.DetailView):
    model = Game

class BrowseView(generic.View):
    pass

class GameListView(generic.View):
    pass

class ForumView(generic.View):
    pass

def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('/')
    else:
        form = SignUpForm()
    return render(request, 'games/register.html', {'form': form})