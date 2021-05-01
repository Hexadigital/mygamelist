from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib.auth import login, authenticate
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Game, Genre, Platform, Tag
from .forms import SignUpForm

def IndexView(request):
    sexual_content = Tag.objects.get(name="Sexual Content")
    return render(request, 'games/index.html', {'latest_games': Game.objects.exclude(tags=sexual_content).order_by('-id')[:25]})

def GamesTaggedWithView(request, tag_id, name=None):
    sexual_content = Tag.objects.get(name="Sexual Content")
    tag = Tag.objects.get(id=tag_id)
    game_list = Game.objects.filter(tags=tag).exclude(tags=sexual_content).order_by('-id')
    page = request.GET.get('page', 1)

    paginator = Paginator(game_list, 25)
    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)
    return render(request, 'games/tag_detail.html', {'game_list': paginated_results, 'tag': tag})

class GenreView(generic.DetailView):
    model = Genre

class PlatformView(generic.DetailView):
    model = Platform

class GameView(generic.DetailView):
    model = Game

def BrowseView(request):
    sexual_content = Tag.objects.get(name="Sexual Content")
    game_list = Game.objects.exclude(tags=sexual_content).order_by('-id')
    page = request.GET.get('page', 1)

    paginator = Paginator(game_list, 25)
    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)
    return render(request, 'games/browse.html', {'game_list': paginated_results})

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