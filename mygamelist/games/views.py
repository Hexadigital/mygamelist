import datetime
from collections import OrderedDict
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q

from .models import Game, Genre, Platform, Tag, User, UserGameListEntry, ManualUserGameListEntry, UserGameStatus
from .models import UserGameStatus, Notification, Recommendation
from .forms import SignUpForm, ManualGameForm, GameEntryForm

def IndexView(request):
    if request.user.is_authenticated:
        status_list = UserGameStatus.objects.filter(user=request.user).order_by('-id')
    else:
        status_list = UserGameStatus.objects.order_by('-id')
    sexual_content = Tag.objects.get(name="Sexual Content")
    latest_games = Game.objects.exclude(tags=sexual_content).order_by('-id')[:8]
    #popular_games = UserGameStatus.objects.exclude(game__tags=sexual_content).values("game", "game__image", "game__name").filter(created_at__lte=datetime.datetime.today(), created_at__gt=datetime.datetime.today()-datetime.timedelta(days=30)).annotate(count=Count('game')).order_by("-count")[:8]
    page = request.GET.get('page', 1)

    paginator = Paginator(status_list, 25)
    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)
    return render(request, 'games/index.html', {'activities': paginated_results, 'latest_games': latest_games})

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
    if tab is None or tab == 'activity':
        status_list = UserGameStatus.objects.filter(user=user_id).order_by('-id')
        page = request.GET.get('page', 1)

        paginator = Paginator(status_list, 25)
        try:
            paginated_results = paginator.page(page)
        except PageNotAnInteger:
            paginated_results = paginator.page(1)
        except EmptyPage:
            paginated_results = paginator.page(paginator.num_pages)
        return render(request, 'games/profile.html', {'selected_user': selected_user, 'tab': tab, 'activities': paginated_results})
    elif tab == "list":
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
    elif tab == "social":
        return render(request, 'games/profile.html', {'selected_user': selected_user, 'tab': tab})
    elif tab == "stats":
        return render(request, 'games/profile.html', {'selected_user': selected_user, 'tab': tab})
    elif tab == "contrib":
        return render(request, 'games/profile.html', {'selected_user': selected_user, 'tab': tab})
    else:
        raise Http404

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
    status_conversion = {
        "PLAY":"Playing",
        "CMPL":"Completed",
        "HOLD":"On Hold",
        "DROP":"Dropped",
        "PLAN":"Plan to Play",
        "IMPT": "Imported"
    }
    game = Game.objects.get(id=game_id)
    game_entries = UserGameListEntry.objects.filter(game=game)
    if request.user.is_authenticated:
        try:
            game_entry = UserGameListEntry.objects.get(game=Game.objects.get(id=game_id),user=request.user)
            game_entry.status = status_conversion[game_entry.status]
        except UserGameListEntry.DoesNotExist:
            game_entry = None
    else:
        game_entry = None
    user_scores = []
    user_counts = {'PLAN':0, 'PLAY':0, 'CMPL':0, 'HOLD':0, 'DROP':0, 'IMPT':0}
    for entry in game_entries:
        if entry.score is not None:
            user_scores.append(entry.score * 10)
        user_counts[entry.status] += 1
    if len(user_scores) > 0:
        return render(request, 'games/game_detail.html', {'game': game, 'user_score':sum(user_scores)/len(user_scores), 'users_rated':len(user_scores), 'user_counts':user_counts, 'game_entry': game_entry})
    else:
        return render(request, 'games/game_detail.html', {'game': game, 'user_score':None, 'users_rated':0, 'user_counts':user_counts, 'game_entry': game_entry})

def BrowseView(request):
    sexual_content = Tag.objects.get(name="Sexual Content")
    query = request.GET.get('search')
    if query:
        game_list = Game.objects.filter(Q(name__icontains=query) | Q(aliases__icontains=query)).exclude(tags=sexual_content).order_by('-id')
    else:
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
            total_list[status_conversion[entry.status]][entry.game.name] = {'id': entry.game.id, 'game_id': entry.game.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed, 'edit_type': 'edit', 'delete_type': 'delete'}
        for entry in manual_list:
            total_list[status_conversion[entry.status]][entry.name] = {'id': entry.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed, 'edit_type': 'edit-manual', 'delete_type': 'delete-manual'}
        # Sort dicts
        for status in total_list.keys():
            total_list[status] = OrderedDict(sorted(total_list[status].items()))
        return render(request, 'games/user_list.html', {'total_list': total_list, 'edit_type': edit_type})
    # Manual game deletion
    elif edit_type == 'delete-manual':
        try:
            game_entry = ManualUserGameListEntry.objects.get(id=entry_id)
        except ManualUserGameListEntry.DoesNotExist:
            raise Http404
        # Does this belong to the logged in user?
        if game_entry.user.id != user_id:
            raise Http404
        if request.method == 'POST':
            game_entry.delete()
            return HttpResponseRedirect('/gamelist/')
        return render(request, 'games/delete_manual_entry.html', {'game_entry': game_entry})
    elif edit_type == 'delete':
        try:
            game = Game.objects.get(id=entry_id)
            game_entry = UserGameListEntry.objects.get(game=game,user=request.user)
        except (Game.DoesNotExist, UserGameListEntry.DoesNotExist):
            raise Http404
        if request.method == 'POST':
            game_entry.delete()
            return HttpResponseRedirect('/gamelist/')
        return render(request, 'games/delete_game_entry.html', {'game_id': entry_id, 'game_entry': game_entry})
    # Manual game edit
    elif edit_type == 'edit-manual':
        try:
            game_entry = ManualUserGameListEntry.objects.get(id=entry_id)
        except ManualUserGameListEntry.DoesNotExist:
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
        try:
            game = Game.objects.get(id=entry_id)
        except Game.DoesNotExist:
            raise Http404
        new = False
        try:
            game_entry = UserGameListEntry.objects.get(game=game,user=request.user)
        except UserGameListEntry.DoesNotExist:
            game_entry = UserGameListEntry()
            game_entry.user = request.user
            game_entry.game = game
            new = True
        if request.method == 'POST':
            # create a form instance and populate it with data from the request:
            form = GameEntryForm(request.POST)
            # check whether it's valid:
            print(form.is_valid())
            print(form.errors)
            if form.is_valid():
                # Update entry
                if (game_entry.status != form.cleaned_data['status']) or new:
                    activity = UserGameStatus()
                    activity.user = request.user
                    activity.game = game
                    activity.status = form.cleaned_data['status']
                    activity.save()
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

@login_required(login_url='/login/')
def NotificationsView(request, action=''):
    notification_list = Notification.objects.filter(user=request.user).order_by('-id')
    if action == "clear":
        notification_list.delete()
        return redirect('/notifications/')
    final_notif_list = []
    for notif in notification_list:
        new_notif = {}
        if notif.notif_type == 'MIGRATED':
            game = Game.objects.get(id=notif.notif_object_id)
            new_notif['created_at'] = notif.created_at
            new_notif['user'] = notif.user
            new_notif['notif_type'] = notif.notif_type
            new_notif['game'] = game
            final_notif_list.append(new_notif)
    return render(request, 'games/notifications.html', {'notification_list': final_notif_list})

@login_required(login_url='/login/')
def RecommendationsView(request, slot=1):
    rec_list = Recommendation.objects.filter(user=request.user).order_by('slot')
    return render(request, 'games/recommendations.html', {'rec_list': rec_list})

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