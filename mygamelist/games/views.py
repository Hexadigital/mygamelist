from collections import OrderedDict
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib.auth import login, authenticate
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Game, Genre, Platform, Tag, User, UserGameListEntry, ManualUserGameListEntry
from .forms import SignUpForm

def IndexView(request):
    return render(request, 'games/index.html', {})

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

def ProfileView(request, user_id, name=None, tab=None):
    selected_user = User.objects.get(id=user_id)
    # Activity
    if tab is None:
        return render(request, 'games/profile.html', {'selected_user': selected_user, 'tab': tab})
    if tab == "list":
        game_list = UserGameListEntry.objects.filter(user=user_id)
        manual_list = ManualUserGameListEntry.objects.filter(user=user_id)
        playing_list = {}
        completed_list = {}
        dropped_list = {}
        hold_list = {}
        planning_list = {}
        for entry in game_list:
            if entry.status == "PLAY":
                playing_list[entry.game.name] = {'game_id': entry.game.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
            elif entry.status == "CMPL":
                completed_list[entry.game.name] = {'game_id': entry.game.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
            elif entry.status == "HOLD":
                hold_list[entry.game.name] = {'game_id': entry.game.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
            elif entry.status == "DROP":
                dropped_list[entry.game.name] = {'game_id': entry.game.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
            elif entry.status == "PLAN":
                planning_list[entry.game.name] = {'game_id': entry.game.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
        for entry in manual_list:
            if entry.status == "PLAY":
                playing_list[entry.name] = {'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
            elif entry.status == "CMPL":
                completed_list[entry.name] = {'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
            elif entry.status == "HOLD":
                hold_list[entry.name] = {'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
            elif entry.status == "DROP":
                dropped_list[entry.name] = {'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
            elif entry.status == "PLAN":
                planning_list[entry.name] = {'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
        # Sort dicts
        playing_list = OrderedDict(sorted(playing_list.items()))
        completed_list = OrderedDict(sorted(completed_list.items()))
        dropped_list = OrderedDict(sorted(dropped_list.items()))
        hold_list = OrderedDict(sorted(hold_list.items()))
        planning_list = OrderedDict(sorted(planning_list.items()))
        
        
        
        return render(request, 'games/profile.html', {'selected_user': selected_user, 'tab': tab, 'playing_list': playing_list, 'completed_list': completed_list,
                                                      'dropped_list': dropped_list, 'hold_list': hold_list, 'planning_list': planning_list})
    if tab == "social":
        return render(request, 'games/profile.html', {'selected_user': selected_user, 'tab': tab})
    if tab == "stats":
        return render(request, 'games/profile.html', {'selected_user': selected_user, 'tab': tab})
    if tab == "contrib":
        return render(request, 'games/profile.html', {'selected_user': selected_user, 'tab': tab})

def GenreView(request, genre_id, name=None):
    sexual_content = Tag.objects.get(name="Sexual Content")
    genre = Genre.objects.get(id=genre_id)
    game_list = Game.objects.filter(genres=genre).exclude(tags=sexual_content).order_by('-id')
    page = request.GET.get('page', 1)

    paginator = Paginator(game_list, 25)
    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)
    return render(request, 'games/genre_detail.html', {'game_list': paginated_results, 'genre': genre})

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