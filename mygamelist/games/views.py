import datetime
import json
import random
from collections import OrderedDict
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q

from .models import Game, Genre, Platform, Tag, User, UserGameListEntry, ManualUserGameListEntry, UserGameStatus
from .models import UserGameStatus, Notification, Recommendation, Collection, CollectionType, UserProfile, UserSettings, TagAdditionRequest
from .forms import SignUpForm, ManualGameForm, GameEntryForm, ChangeAvatarForm, ChangeIgnoredTagsForm, TagAdditionRequestForm

def IndexView(request):
    banned_tags = [Tag.objects.get(name="Sexual Content").id]
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            banned_tags = [x.id for x in user_profile.banned_tags.all()]
            followed_users = [x.id for x in user_profile.followed_users.all()]
            followed_users.append(request.user.id)
            status_list = UserGameStatus.objects.filter(user__in=followed_users).order_by('-id')
        except UserProfile.DoesNotExist:
            status_list = UserGameStatus.objects.filter(user=request.user).order_by('-id')
    else:
        status_list = UserGameStatus.objects.order_by('-id')
    latest_games = Game.objects.exclude(tags__in=banned_tags).order_by('-id')[:8]
    #popular_games = UserGameStatus.objects.exclude(tags__in=banned_tags).values("game", "game__image", "game__name").filter(created_at__lte=datetime.datetime.today(), created_at__gt=datetime.datetime.today()-datetime.timedelta(days=30)).annotate(count=Count('game')).order_by("-count")[:8]
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
    banned_tags = [Tag.objects.get(name="Sexual Content").id]
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        banned_tags = [x.id for x in user_profile.banned_tags.all()]
    try:
        tag = Tag.objects.get(id=tag_id)
    except Tag.DoesNotExist:
        raise Http404
    game_list = Game.objects.filter(tags=tag).exclude(tags__in=banned_tags).order_by('-id')
    page = request.GET.get('page', 1)

    paginator = Paginator(game_list, 25)
    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)
    return render(request, 'games/tag_detail.html', {'game_list': paginated_results, 'tag': tag})

def GamesInCollectionView(request, col_id, name=None):
    banned_tags = [Tag.objects.get(name="Sexual Content").id]
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        banned_tags = [x.id for x in user_profile.banned_tags.all()]
    try:
        collection = Collection.objects.get(id=col_id)
    except Collection.DoesNotExist:
        raise Http404
    game_list = collection.games.exclude(tags__in=banned_tags).order_by('-id')
    page = request.GET.get('page', 1)

    paginator = Paginator(game_list, 25)
    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)
    return render(request, 'games/collection_list.html', {'game_list': paginated_results, 'collection': collection})

@login_required(login_url='/login/')
def GameListRandomView(request):
    game_list = UserGameListEntry.objects.filter(user=request.user.id,status='PLAN')
    manual_list = ManualUserGameListEntry.objects.filter(user=request.user.id,status='PLAN')
    planning = []
    for entry in game_list:
        planning.append({'name':entry.game.name, 'platform':entry.platform, 'comments':entry.comments, 'id':entry.game.id})
    for entry in manual_list:
        planning.append({'name':entry.name, 'platform':entry.platform, 'comments':entry.comments, 'id':None})
    
    return render(request, 'games/random_from_list.html', random.choice(planning))

def ProfileView(request, user_id, name=None, tab=None):
    try:
        selected_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise Http404
    followed = False
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            followed_users = [x.id for x in user_profile.followed_users.all()]
            if selected_user.id in followed_users:
                followed = True
        except UserProfile.DoesNotExist:
            pass
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
        return render(request, 'games/profile.html', {'selected_user': selected_user, 'followed': followed, 'tab': tab, 'activities': paginated_results})
    elif tab == "list":
        status_conversion = {
            "PLAY":"Playing",
            "CMPL":"Completed",
            "HOLD":"Paused",
            "DROP":"Dropped",
            "PLAN":"Plan to Play",
            "IMPT": "Imported"
        }
        game_list = UserGameListEntry.objects.filter(user=user_id)
        manual_list = ManualUserGameListEntry.objects.filter(user=user_id)
        total_list = {"Playing": {}, "Completed": {}, "Paused": {}, "Dropped": {}, "Plan to Play": {}, "Imported": {}}
        for entry in game_list:
            total_list[status_conversion[entry.status]][entry.game.name] = {'game_id': entry.game.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
        for entry in manual_list:
            total_list[status_conversion[entry.status]][entry.name] = {'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
        # Sort dicts
        for status in total_list.keys():
            total_list[status] = OrderedDict(sorted(total_list[status].items()))
            
        # Figure out how to display their ratings
        try:
            user_settings = UserSettings.objects.get(user=selected_user)
            profile_score_type = user_settings.score_type
        except UserSettings.DoesNotExist:
            profile_score_type = None

        return render(request, 'games/profile.html', {'selected_user': selected_user, 'followed': followed, 'tab': tab, 'total_list': total_list, 'profile_score_type': profile_score_type})
    elif tab == "social":
        followed_by = User.objects.filter(userprofile__followed_users=selected_user).all()
        return render(request, 'games/profile.html', {'selected_user': selected_user, 'followed': followed, 'followed_by': followed_by, 'tab': tab})
    elif tab == "stats":
        return render(request, 'games/profile.html', {'selected_user': selected_user, 'followed': followed, 'tab': tab})
    elif tab == "contrib":
        return render(request, 'games/profile.html', {'selected_user': selected_user, 'followed': followed, 'tab': tab})
    else:
        raise Http404

def GenreView(request, genre_id, name=None):
    banned_tags = [Tag.objects.get(name="Sexual Content").id]
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        banned_tags = [x.id for x in user_profile.banned_tags.all()]
    try:
        genre = Genre.objects.get(id=genre_id)
    except Genre.DoesNotExist:
        raise Http404
    game_list = Game.objects.filter(genres=genre).exclude(tags__in=banned_tags).order_by('-id')
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

@login_required(login_url='/login/')
def IgnoreGameView(request, game_id):
    rec = None
    try:
        game = Game.objects.get(id=game_id)
    except Game.DoesNotExist:
        raise Http404
    try:
        rec = Recommendation.objects.filter(user=request.user, game=game)
    except Recommendation.DoesNotExist:
        pass
    try:
        if game in request.user.userprofile.ignored_games.all():
            request.user.userprofile.ignored_games.remove(game)
        else:
            request.user.userprofile.ignored_games.add(game)
            if rec is not None:
                rec.delete()
    except Exception as e:
        print(e)
    return HttpResponseRedirect('/game/' + str(game_id))

@login_required(login_url='/login/')
def FollowUserView(request, user_id):
    rec = None
    try:
        req_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise Http404
    try:
        if req_user in request.user.userprofile.followed_users.all():
            request.user.userprofile.followed_users.remove(req_user)
        else:
            request.user.userprofile.followed_users.add(req_user)
            new_notif = Notification()
            new_notif.user = req_user
            new_notif.notif_type = 'FOLLOWED'
            new_notif.notif_object_id = request.user.id
            new_notif.save()
    except Exception as e:
        print(e)
    return HttpResponseRedirect('/user/' + str(req_user.id))

def GameView(request, game_id, name=None):
    status_conversion = {
        "PLAY":"Playing",
        "CMPL":"Completed",
        "HOLD":"Paused",
        "DROP":"Dropped",
        "PLAN":"Plan to Play",
        "IMPT": "Imported"
    }
    try:
        game = Game.objects.get(id=game_id)
    except Game.DoesNotExist:
        raise Http404

    user_col_type = CollectionType.objects.get(name='User')
    regular_collections = Collection.objects.exclude(category=user_col_type).filter(games=game).order_by('category', 'name')
    user_collections = Collection.objects.filter(category=user_col_type).filter(games=game).order_by('category', 'name')

    stubbed = False
    if "STUB" in [x.name for x in game.tags.all()]:
        stubbed = True

    game_entries = UserGameListEntry.objects.filter(game=game)
    game_entry = None
    ignored = False
    if request.user.is_authenticated:
        try:
            if game in request.user.userprofile.ignored_games.all():
                ignored = True
            game_entry = UserGameListEntry.objects.get(game=Game.objects.get(id=game_id),user=request.user)
            game_entry.status = status_conversion[game_entry.status]
        except UserGameListEntry.DoesNotExist:
            game_entry = None
    user_scores = []
    user_counts = {'PLAN':0, 'PLAY':0, 'CMPL':0, 'HOLD':0, 'DROP':0, 'IMPT':0}
    for entry in game_entries:
        if entry.score is not None:
            user_scores.append(entry.score * 10)
        user_counts[entry.status] += 1
    if len(user_scores) > 0:
        return render(request, 'games/game_detail.html', {'game': game, 'user_score':sum(user_scores)/len(user_scores), 'users_rated':len(user_scores), 'user_counts':user_counts, 'game_entry': game_entry, 'regular_collections':regular_collections, 'user_collections':user_collections, 'stubbed':stubbed, 'ignored':ignored})
    else:
        return render(request, 'games/game_detail.html', {'game': game, 'user_score':None, 'users_rated':0, 'user_counts':user_counts, 'game_entry': game_entry, 'regular_collections':regular_collections, 'user_collections':user_collections, 'stubbed':stubbed, 'ignored':ignored})

def BrowseView(request):
    banned_tags = [Tag.objects.get(name="Sexual Content").id]
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        banned_tags = [x.id for x in user_profile.banned_tags.all()]
    query = request.GET.get('search')
    if query:
        game_list = Game.objects.filter(Q(name__icontains=query) | Q(aliases__icontains=query)).exclude(tags__in=banned_tags).order_by('-id')
    else:
        game_list = Game.objects.exclude(tags__in=banned_tags).order_by('-id')
    page = request.GET.get('page', 1)

    paginator = Paginator(game_list, 25)
    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)
    return render(request, 'games/browse.html', {'game_list': paginated_results})

def BrowseCollectionView(request):
    query = request.GET.get('search')
    if query:
        collection_list = Collection.objects.filter(Q(name__icontains=query)).order_by('-id')
    else:
        collection_list = Collection.objects.order_by('-id')
    page = request.GET.get('page', 1)

    paginator = Paginator(collection_list, 25)
    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)
    return render(request, 'games/search_for_collection.html', {'collection_list': paginated_results})

def BrowseUserView(request):
    query = request.GET.get('search')
    if query:
        user_list = User.objects.filter(Q(name__icontains=query)).order_by('-id')
    else:
        user_list = User.objects.order_by('-id')
    page = request.GET.get('page', 1)

    paginator = Paginator(user_list, 25)
    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)
    return render(request, 'games/search_for_user.html', {'user_list': paginated_results})

@login_required(login_url='/login/')
def GameListView(request, edit_type=None, entry_id=None):
    status_conversion = {
        "PLAY":"Playing",
        "CMPL":"Completed",
        "HOLD":"Paused",
        "DROP":"Dropped",
        "PLAN":"Plan to Play",
        "IMPT": "Imported"
    }
    user_id = request.user.id
    # Viewing list
    if edit_type is None:
        game_list = UserGameListEntry.objects.filter(user=user_id)
        manual_list = ManualUserGameListEntry.objects.filter(user=user_id)
        total_list = {"Playing": {}, "Completed": {}, "Paused": {}, "Dropped": {}, "Plan to Play": {}, "Imported": {}}
        for entry in game_list:
            total_list[status_conversion[entry.status]][entry.game.name] = {'id': entry.game.id, 'game_id': entry.game.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed, 'edit_type': 'edit', 'delete_type': 'delete'}
        for entry in manual_list:
            total_list[status_conversion[entry.status]][entry.name] = {'id': entry.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed, 'edit_type': 'edit-manual', 'delete_type': 'delete-manual', 'never_migrate':entry.never_migrate}
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
        rec = None
        try:
            game = Game.objects.get(id=entry_id)
        except Game.DoesNotExist:
            raise Http404
        try:
            rec = Recommendation.objects.filter(user=request.user, game=game)
        except Recommendation.DoesNotExist:
            pass
        new = False
        try:
            game_entry = UserGameListEntry.objects.get(game=game,user=request.user)
        except UserGameListEntry.DoesNotExist:
            game_entry = UserGameListEntry()
            game_entry.user = request.user
            game_entry.game = game
            new = True
        if request.method == 'POST':
            if game in request.user.userprofile.ignored_games.all():
                request.user.userprofile.ignored_games.remove(game)
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
                if rec is not None:
                    rec.delete()
                return HttpResponseRedirect('/game/' + str(game.id))
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
        elif notif.notif_type == 'FOLLOWED':
            follower = User.objects.get(id=notif.notif_object_id)
            new_notif['user'] = notif.user
            new_notif['notif_type'] = notif.notif_type
            new_notif['follower'] = follower
            final_notif_list.append(new_notif)
    return render(request, 'games/notifications.html', {'notification_list': final_notif_list})

@login_required(login_url='/login/')
def RecommendationsView(request, user_id=None):
    if request.user.id == 1 and user_id is not None:
        selected_user = User.objects.get(id=user_id)
        rec_list = Recommendation.objects.filter(user=selected_user).order_by('slot')
    else:
        rec_list = Recommendation.objects.filter(user=request.user).order_by('slot')
    return render(request, 'games/recommendations.html', {'rec_list': rec_list})

@login_required(login_url='/login/')
def RecommendationsRefreshView(request):
    rec_list = Recommendation.objects.filter(user=request.user).order_by('slot')
    rec_list.delete()
    with open("/home/mygamelist/rec-queue/" + str(request.user.id), "w") as out_file:
        out_file.write("refresh")
    return redirect('/recommendations/')

@login_required(login_url='/login/')
def LikeStatusView(request, status_id=None):
    try:
        status = UserGameStatus.objects.get(id=status_id)
    except UserGameStatus.DoesNotExist:
        raise Http404
    # Handle like action
    js_response = {}
    if request.user in status.liked_by.all():
        js_response['liked'] = False
        status.liked_by.remove(request.user)
    else:
        js_response['liked'] = True
        status.liked_by.add(request.user)
    # Return JSON for JavaScript requests
    if request.is_ajax():
        js_response['new_count'] = status.liked_by.count()
        return HttpResponse(json.dumps(js_response), content_type='application/json')
    else:
        return redirect('/')

@login_required(login_url='/login/')
def SettingsView(request):
    return render(request, 'games/settings.html', {})

@login_required(login_url='/login/')
def ChangeAvatarView(request):
    form = ChangeAvatarForm()
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = ChangeAvatarForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('/settings')
    return render(request, 'games/avatar_change.html', {'form':form})

@login_required(login_url='/login/')
def ChangeIgnoredTagsView(request):
    user_profile = UserProfile.objects.get(user=request.user)
    banned_tags = [x.id for x in user_profile.banned_tags.all()]
    form = ChangeIgnoredTagsForm(instance=user_profile)
    if request.method == 'POST':
        form = ChangeIgnoredTagsForm(request.POST, instance=user_profile)
        print(form.is_valid())
        if form.is_valid():
            form.save()
            return redirect('/settings')
    tags = {"Content":[],"Mechanics":[],"Protagonist":[],"Setting":[],"Subgenre":[],
           "Graphics":[],"Meta":[],"Narrative":[],"Sports":[],"Technical":[]}
    for tag in Tag.objects.all():
        if tag.category in tags.keys():
            tags[tag.category].append({'id':tag.id, 'name':tag.name})
    return render(request, 'games/change_ignored_tags.html', {'tags':tags, 'banned_tags':banned_tags, 'form':form})

@login_required(login_url='/login/')
def TagAdditionRequestView(request, game_id):
    try:
        game = Game.objects.get(id=game_id)
    except Game.DoesNotExist:
        raise Http404
    form = TagAdditionRequestForm()
    if request.method == 'POST':
        form = TagAdditionRequestForm(request.POST)
        if form.is_valid():
            tagreq = TagAdditionRequest()
            tagreq.game = game
            tagreq.requested_by = request.user
            tagreq.tag = form.cleaned_data['tag']
            tagreq.comments = form.cleaned_data['comments']
            tagreq.save()
            return redirect('/game/' + str(game_id))
    return render(request, 'games/submit_tag.html', {'game':game, 'form':form})

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