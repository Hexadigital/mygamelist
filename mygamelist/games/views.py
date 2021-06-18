from collections import OrderedDict
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Game, Genre, Platform, Tag, User, UserGameListEntry, ManualUserGameListEntry
from .forms import SignUpForm, ManualGameForm, GameEntryForm

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

def GameView(request, game_id, name=None):
    game = Game.objects.get(id=game_id)
    game_entries = UserGameListEntry.objects.filter(game=game)
    user_scores = []
    for entry in game_entries:
        if entry.score is not None:
            user_scores.append(entry.score * 10)
    if len(user_scores) > 0:
        return render(request, 'games/game_detail.html', {'game': game, 'user_score':sum(user_scores)/len(user_scores), 'users_rated':len(user_scores)})
    else:
        return render(request, 'games/game_detail.html', {'game': game, 'user_score':None, 'users_rated':0})

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
def GameListView(request, edit_type=None, entry_id=None):
    status_conversion = {
        "PLAY":"Playing",
        "CMPL":"Completed",
        "HOLD":"On Hold",
        "DROP":"Dropped",
        "PLAN":"Plan to Play",
        "IMPT": "Imported"
    }
    user_id = request.user.id
    # Viewing list
    if edit_type is None:
        game_list = UserGameListEntry.objects.filter(user=user_id)
        manual_list = ManualUserGameListEntry.objects.filter(user=user_id)
        total_list = {"Playing": {}, "Completed": {}, "On Hold": {}, "Dropped": {}, "Plan to Play": {}, "Imported": {}}
        for entry in game_list:
            total_list[status_conversion[entry.status]][entry.game.name] = {'id': entry.game.id, 'game_id': entry.game.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed, 'edit_type': 'edit'}
        for entry in manual_list:
            total_list[status_conversion[entry.status]][entry.name] = {'id': entry.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed, 'edit_type': 'edit-manual'}
        # Sort dicts
        for status in total_list.keys():
            total_list[status] = OrderedDict(sorted(total_list[status].items()))
        return render(request, 'games/user_list.html', {'total_list': total_list, 'edit_type': edit_type})
    # Manual game edit
    elif edit_type == 'edit-manual':
        game_entry = ManualUserGameListEntry.objects.get(id=entry_id)
        # Does this entry exist?
        if game_entry is None:
            raise Http404
        # Does this belong to the logged in user?
        if game_entry.user.id != user_id:
            raise Http404
        if request.method == 'POST':
            # create a form instance and populate it with data from the request:
            form = ManualGameForm(request.POST)
            # check whether it's valid:
            print(form.is_valid())
            print(form.errors)
            if form.is_valid():
                # Update entry
                game_entry.name = form.cleaned_data['name']
                game_entry.platform = form.cleaned_data['platform']
                game_entry.status = form.cleaned_data['status']
                if form.cleaned_data['score'] == 0.0 or form.cleaned_data['score'] == None:
                    game_entry.score = None
                else:
                    game_entry.score = max(min(form.cleaned_data['score'], 10.00), 0.00)
                if form.cleaned_data['hours'] == 0.0 or form.cleaned_data['hours'] == None:
                    game_entry.hours = None
                else:
                    game_entry.hours = form.cleaned_data['hours']
                game_entry.comments = form.cleaned_data['comments']
                game_entry.start_date = form.cleaned_data['start_date']
                game_entry.stop_date = form.cleaned_data['stop_date']
                game_entry.times_replayed = max(min(form.cleaned_data['times_replayed'], 999), 0)
                game_entry.save()
                return HttpResponseRedirect('/gamelist/')
        else:
            form = ManualGameForm()
        return render(request, 'games/edit_manual_game.html', {'form': form, 'game_entry': game_entry})
    elif edit_type == 'edit':
        game_entry = UserGameListEntry.objects.get(game=Game.objects.get(id=entry_id),user=request.user)
        # Does this entry exist?
        if game_entry is None:
            raise Http404
        if request.method == 'POST':
            # create a form instance and populate it with data from the request:
            form = GameEntryForm(request.POST)
            # check whether it's valid:
            print(form.is_valid())
            print(form.errors)
            if form.is_valid():
                # Update entry
                game_entry.platform = form.cleaned_data['platform']
                game_entry.status = form.cleaned_data['status']
                if form.cleaned_data['score'] == 0.0 or form.cleaned_data['score'] == None:
                    game_entry.score = None
                else:
                    game_entry.score = max(min(form.cleaned_data['score'], 10.00), 0.00)
                if form.cleaned_data['hours'] == 0.0 or form.cleaned_data['hours'] == None:
                    game_entry.hours = None
                else:
                    game_entry.hours = form.cleaned_data['hours']
                game_entry.comments = form.cleaned_data['comments']
                game_entry.start_date = form.cleaned_data['start_date']
                game_entry.stop_date = form.cleaned_data['stop_date']
                game_entry.times_replayed = max(min(form.cleaned_data['times_replayed'], 999), 0)
                game_entry.save()
                return HttpResponseRedirect('/gamelist/')
        else:
            form = ManualGameForm()
        return render(request, 'games/edit_game_entry.html', {'form': form, 'game_id': entry_id, 'game_entry': game_entry})
    elif edit_type == 'add-manual':
        if request.method == 'POST':
            # create a form instance and populate it with data from the request:
            form = ManualGameForm(request.POST)
            # check whether it's valid:
            if form.is_valid():
                # Create entry
                game_entry = ManualUserGameListEntry()
                game_entry.user = request.user
                game_entry.name = form.cleaned_data['name']
                game_entry.platform = form.cleaned_data['platform']
                game_entry.status = form.cleaned_data['status']
                if form.cleaned_data['score'] == 0.0 or form.cleaned_data['score'] == None:
                    game_entry.score = None
                else:
                    game_entry.score = max(min(form.cleaned_data['score'], 10.00), 0.00)
                if form.cleaned_data['hours'] == 0.0 or form.cleaned_data['hours'] == None:
                    game_entry.hours = None
                else:
                    game_entry.hours = form.cleaned_data['hours']
                game_entry.comments = form.cleaned_data['comments']
                game_entry.start_date = form.cleaned_data['start_date']
                game_entry.stop_date = form.cleaned_data['stop_date']
                game_entry.times_replayed = max(min(form.cleaned_data['times_replayed'], 999), 0)
                game_entry.save()
                return HttpResponseRedirect('/gamelist/')
        else:
            form = ManualGameForm()
        return render(request, 'games/add_manual_game.html', {'form': form})
    else:
        raise Http404

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