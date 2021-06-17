from collections import OrderedDict
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
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
        status_conversion = {
            "PLAY":"Playing",
            "CMPL":"Completed",
            "HOLD":"On Hold",
            "DROP":"Dropped",
            "PLAN":"Plan to Play",
            "IMPT": "Imported"
        }
        game_list = UserGameListEntry.objects.filter(user=user_id)
        manual_list = ManualUserGameListEntry.objects.filter(user=user_id)
        total_list = {"Playing": {}, "Completed": {}, "On Hold": {}, "Dropped": {}, "Plan to Play": {}, "Imported": {}}
        for entry in game_list:
            total_list[status_conversion[entry.status]][entry.game.name] = {'game_id': entry.game.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
        for entry in manual_list:
            total_list[status_conversion[entry.status]][entry.name] = {'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
        # Sort dicts
        for status in total_list.keys():
            total_list[status] = OrderedDict(sorted(total_list[status].items()))

        return render(request, 'games/profile.html', {'selected_user': selected_user, 'tab': tab, 'total_list': total_list})
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

@login_required(login_url='/login/')
def GameListView(request):
    status_conversion = {
        "PLAY":"Playing",
        "CMPL":"Completed",
        "HOLD":"On Hold",
        "DROP":"Dropped",
        "PLAN":"Plan to Play",
        "IMPT": "Imported"
    }
    user_id = request.user.id
    game_list = UserGameListEntry.objects.filter(user=user_id)
    manual_list = ManualUserGameListEntry.objects.filter(user=user_id)
    total_list = {"Playing": {}, "Completed": {}, "On Hold": {}, "Dropped": {}, "Plan to Play": {}, "Imported": {}}
    for entry in game_list:
        total_list[status_conversion[entry.status]][entry.game.name] = {'game_id': entry.game.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
    for entry in manual_list:
        total_list[status_conversion[entry.status]][entry.name] = {'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
    # Sort dicts
    for status in total_list.keys():
        total_list[status] = OrderedDict(sorted(total_list[status].items()))
    return render(request, 'games/user_list.html', {'total_list': total_list})

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