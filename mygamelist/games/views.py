import datetime
import json
import random
from collections import OrderedDict
from decimal import Decimal
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.utils.http import is_safe_url

from .models import Game, Genre, Platform, Tag, User, UserGameListEntry, ManualUserGameListEntry, UserGameStatus, UserGameAspectRating
from .models import UserGameStatus, Notification, Recommendation, Collection, CollectionType, UserProfile, UserSettings, TagAdditionRequest, CustomList
from .forms import SignUpForm, ManualGameForm, GameEntryForm, ChangeAvatarForm, ChangeIgnoredTagsForm, TagAdditionRequestForm, CustomListForm, HidePlatformsForm

def IndexView(request, global_view=False):
    banned_tags = [Tag.objects.get(name="Sexual Content").id]
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            banned_tags = [x.id for x in user_profile.banned_tags.all()]
            followed_users = [x.id for x in user_profile.followed_users.all()]
            followed_users.append(request.user.id)
            if global_view:
                status_list = UserGameStatus.objects.prefetch_related('game').prefetch_related('liked_by').prefetch_related('user__userprofile').order_by('-id')
            else:
                status_list = UserGameStatus.objects.filter(user__in=followed_users).prefetch_related('game').prefetch_related('liked_by').prefetch_related('user__userprofile').order_by('-id')
        except UserProfile.DoesNotExist:
            status_list = UserGameStatus.objects.filter(user=request.user).prefetch_related('game').prefetch_related('liked_by').prefetch_related('user__userprofile').order_by('-id')
    else:
        status_list = UserGameStatus.objects.prefetch_related('game').prefetch_related('liked_by').prefetch_related('user__userprofile').order_by('-id')
    status_list = status_list.exclude(game__tags__in=banned_tags)
    latest_games = Game.objects.exclude(tags__in=banned_tags).order_by('-id')[:8]
    popular_games = UserGameStatus.objects.prefetch_related('game').exclude(game__tags__in=banned_tags).values("game", "game__image", "game__name").filter(created_at__lte=datetime.datetime.today(), created_at__gt=datetime.datetime.today()-datetime.timedelta(days=7)).annotate(count=Count('game')).order_by("-count")[:8]
    page = request.GET.get('page', 1)

    paginator = Paginator(status_list, 25)
    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)
    return render(request, 'games/index.html', {'activities': paginated_results, 'latest_games': latest_games, 'popular_games': popular_games, 'global_view': global_view})

def GlobalIndexView(request):
	return IndexView(request, global_view=True)

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

def GamesInCustomListView(request, list_id):
    banned_tags = [Tag.objects.get(name="Sexual Content").id]
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        banned_tags = [x.id for x in user_profile.banned_tags.all()]
    try:
        customlist = CustomList.objects.get(id=list_id)
    except CustomList.DoesNotExist:
        raise Http404
    # Prevent other users from viewing private lists
    if customlist.privacy_level == 'PRIV':
        if request.user.is_authenticated:
            if request.user.id != customlist.user.id:
                return render(request, 'games/error_message.html', {'error':'This list is private!'})
        else:
            return render(request, 'games/error_message.html', {'error':'This list is private!'})
    game_list = customlist.games.exclude(tags__in=banned_tags).order_by('name')
    page = request.GET.get('page', 1)

    paginator = Paginator(game_list, 25)
    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)
    return render(request, 'games/custom_list.html', {'game_list': paginated_results, 'customlist': customlist})

@login_required(login_url='/login/')
def GameListRandomView(request):
    game_list = UserGameListEntry.objects.filter(user=request.user.id,status='PLAN')
    manual_list = ManualUserGameListEntry.objects.filter(user=request.user.id,status='PLAN')
    planning = []
    for entry in game_list:
        planning.append({'name':entry.game.name, 'platform':entry.platform, 'comments':entry.comments, 'id':entry.game.id})
    for entry in manual_list:
        planning.append({'name':entry.name, 'platform':entry.platform, 'comments':entry.comments, 'id':None})
    
    if len(planning) > 0:
        return render(request, 'games/random_from_list.html', random.choice(planning))
    else:
        return render(request, 'games/random_from_list.html', {'name':None})

def ProfileView(request, user_id, name=None, tab=None):
    try:
        selected_user = User.objects.prefetch_related('userprofile__followed_users__userprofile').get(id=user_id)
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
        banned_tags = [Tag.objects.get(name="Sexual Content").id]
        if request.user.is_authenticated:
            user_profile = UserProfile.objects.get(user=request.user)
            banned_tags = [x.id for x in user_profile.banned_tags.all()]
        status_list = UserGameStatus.objects.filter(user=user_id).prefetch_related('game').prefetch_related('user__userprofile').order_by('-id')
        status_list = status_list.exclude(game__tags__in=banned_tags)
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
        game_list = UserGameListEntry.objects.prefetch_related('platform').prefetch_related('game').filter(user=user_id)
        manual_list = ManualUserGameListEntry.objects.prefetch_related('platform').filter(user=user_id)
        total_list = {"Playing": {}, "Completed": {}, "Paused": {}, "Dropped": {}, "Plan to Play": {}, "Imported": {}}
        for entry in game_list:
            total_list[status_conversion[entry.status]][entry.game.name] = {'game_id': entry.game.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
        for entry in manual_list:
            total_list[status_conversion[entry.status]][entry.name] = {'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed}
        # Sort dicts
        for status in total_list.keys():
            # TODO: Find a more elegant way to sort one key reversed and the other normally
            sortingmethod = request.GET.get('sort')
            if sortingmethod and sortingmethod in ['score', 'platform', 'hours']:
                templist = []
                for x in total_list[status].keys():
                    if sortingmethod == 'score':
                        templist.append((Decimal(11) if total_list[status][x]['score'] is None else 10 - total_list[status][x]['score'], x, total_list[status][x]))
                    if sortingmethod == 'platform':
                        if total_list[status][x]['platform'] is None:
                            platform = 'None'
                        else:
                            if total_list[status][x]['platform'].shorthand:
                                platform = total_list[status][x]['platform'].shorthand
                            else:
                                platform = total_list[status][x]['platform'].name
                        templist.append((platform, x, total_list[status][x]))
                    if sortingmethod == 'hours':
                        templist.append((10000000000 if total_list[status][x]['hours'] is None else 10000000000 - total_list[status][x]['hours'], x, total_list[status][x]))
                templist.sort()
                total_list[status].clear()
                for x in templist:
                    total_list[status][x[1]] = x[2]
            else:
                total_list[status] = OrderedDict(sorted(total_list[status].items()))
            
        # Figure out how to display their ratings
        try:
            user_settings = UserSettings.objects.get(user=selected_user)
            profile_score_type = user_settings.score_type
        except UserSettings.DoesNotExist:
            profile_score_type = None

        return render(request, 'games/profile.html', {'selected_user': selected_user, 'followed': followed, 'tab': tab, 'total_list': total_list, 'profile_score_type': profile_score_type})
    elif tab == "clist":
        lists = CustomList.objects.filter(user=selected_user, privacy_level='PUBL').order_by('name')
        return render(request, 'games/profile.html', {'selected_user': selected_user, 'followed': followed, 'tab': tab, 'clists': lists})
    elif tab == "social":
        followed_by = User.objects.prefetch_related('userprofile').filter(userprofile__followed_users=selected_user).all()
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

def BetterView(request, better_type=None):
    banned_tags = [Tag.objects.get(name="Sexual Content").id]
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        banned_tags = [x.id for x in user_profile.banned_tags.all()]
    query = request.GET.get('search')
    if better_type is None:
        return render(request, 'games/better.html')
    elif better_type == 'description':
        game_list = Game.objects.filter(description__exact='').exclude(tags__in=banned_tags).order_by('-id')
        page_title = 'Games Missing Descriptions'
        page_description = 'A list of games that still need a description.'
        page_header = 'Games Needing Descriptions:'
    elif better_type == 'screens':
        screenshot_filter = Q(screen1__isnull=False) & Q(screen2__isnull=False) & Q(screen3__isnull=False) & Q(screen4__isnull=False)
        game_list = Game.objects.exclude(screenshot_filter).exclude(tags__in=banned_tags).order_by('-id')
        page_title = 'Games Missing Screenshots'
        page_description = 'A list of games that have less than four screenshots.'
        page_header = 'Games Needing Screenshots:'
    elif better_type == 'no-screens':
        screenshot_filter = Q(screen1__isnull=True) & Q(screen2__isnull=True) & Q(screen3__isnull=True) & Q(screen4__isnull=True)
        game_list = Game.objects.filter(screenshot_filter).exclude(tags__in=banned_tags).order_by('-id')
        page_title = 'Games Without Any Screenshots'
        page_description = 'A list of games that have no screenshots.'
        page_header = 'Games Without Screenshots:'
    elif better_type == 'video':
        game_list = Game.objects.filter(trailer_link__exact='').exclude(tags__in=banned_tags).order_by('-id')
        page_title = 'Games Missing Video'
        page_description = 'A list of games that still need a video.'
        page_header = 'Games Needing Video:'
    else:
        raise Http404

    page = request.GET.get('page', 1)
    paginator = Paginator(game_list, 25)
    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)
    return render(request, 'games/browse_nosearch.html', {'game_list': paginated_results, 'page_title': page_title, 'page_description': page_description, 'page_header': page_header})

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

def GameView(request, game_id, name=None, tab=None):
    status_conversion = {
        "PLAY":"Playing",
        "CMPL":"Completed",
        "HOLD":"Paused",
        "DROP":"Dropped",
        "PLAN":"Plan to Play",
        "IMPT": "Imported"
    }
    try:
        game = Game.objects.prefetch_related('genres').prefetch_related('tags').get(id=game_id)
    except Game.DoesNotExist:
        raise Http404

    banned_tags = [Tag.objects.get(name="Sexual Content").id]
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        banned_tags = [x.id for x in user_profile.banned_tags.all()]

    game_tags = game.tags.all()
    for tag_id in [x.id for x in game_tags]:
        if tag_id in banned_tags:
            return render(request, 'games/error_message.html', {'error':'This game has one or more of your ignored tags!', 'suberror':'You can edit your ignored tags via your settings.'})

    # Fetch pending tag submissions
    pending_tags = TagAdditionRequest.objects.filter(game=game).prefetch_related('tag')

    # Fetch user-specific information for left sidebar
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

    # Fetch general information for left sidebar
    game_entries = UserGameListEntry.objects.filter(game=game)
    user_scores = []
    user_counts = {'PLAN':0, 'PLAY':0, 'CMPL':0, 'HOLD':0, 'DROP':0, 'IMPT':0}
    for entry in game_entries:
        if entry.score is not None:
            user_scores.append(entry.score * 10)
        user_counts[entry.status] += 1
    if len(user_scores) > 0:
        user_score = sum(user_scores)/len(user_scores)
        users_rated = len(user_scores)
    else:
        user_score = None
        users_rated = 0


    # Determine whether or not this page still needs tags
    stubbed = False
    if len(game_tags) < 5:
        stubbed = True

    # Overview tab
    if tab is None:
        user_col_type = CollectionType.objects.get(name='User')
        regular_collections = Collection.objects.prefetch_related('category').exclude(category=user_col_type).filter(games=game).order_by('category', 'name')
        user_collections = Collection.objects.prefetch_related('category').filter(category=user_col_type).filter(games=game).order_by('category', 'name')

        if 'watch?v=' in game.trailer_link:
            game.trailer_link = game.trailer_link.split("watch?v=")[1]
        return render(request, 'games/game_detail.html', {'game': game, 'pending_tags':pending_tags, 'user_score':user_score, 'users_rated':users_rated, 'user_counts':user_counts, 'game_entry': game_entry, 'regular_collections':regular_collections, 'user_collections':user_collections, 'stubbed':stubbed, 'ignored':ignored, 'tab':tab})
    # Social tab
    elif tab == 'social':
        # Find recent activity
        recent_statuses = UserGameStatus.objects.filter(game=game).prefetch_related('liked_by').prefetch_related('user__userprofile').order_by('-id')[:8]
        # Find list entries from followed users
        if request.user.is_authenticated:
            followed_users = [x.id for x in user_profile.followed_users.all()]
            followed_users.append(request.user.id)
            following_entries = UserGameListEntry.objects.filter(user__in=followed_users).prefetch_related('user__userprofile').prefetch_related('user__usersettings').filter(game=game).order_by('user__username')
        else:
            following_entries = []
        return render(request, 'games/game_detail.html', {'game': game, 'pending_tags':pending_tags, 'user_score':user_score, 'users_rated':users_rated, 'user_counts':user_counts, 'game_entry': game_entry, 'recent_statuses': recent_statuses, 'following_entries': following_entries, 'stubbed':stubbed, 'ignored':ignored, 'tab':tab})
    elif tab == 'aspects':
        # Calculate site aspects
        ratings = UserGameAspectRating.objects.filter(game=game)
        try:
            personal_rating = UserGameAspectRating.objects.get(game=game, user=request.user)
        except:
            personal_rating = None
        rating_dict = {}
        difficulty_total = 0
        difficulty_count = 0
        replayability_total = 0
        replayability_count = 0
        graphics_total = 0
        graphics_count = 0
        audio_total = 0
        audio_count = 0
        story_total = 0
        story_count = 0
        recommendability_total = 0
        recommendability_count = 0
        for rating in ratings:
            if rating.difficulty != 0:
                difficulty_total += rating.difficulty
                difficulty_count += 1
            if rating.replayability != 0:
                replayability_total += rating.replayability
                replayability_count += 1
            if rating.graphics != 0:
                graphics_total += rating.graphics
                graphics_count += 1
            if rating.audio != 0:
                audio_total += rating.audio
                audio_count += 1
            if rating.story != 0:
                story_total += rating.story
                story_count += 1
            if rating.recommendability != 0:
                recommendability_total += rating.recommendability
                recommendability_count += 1
        if difficulty_count == 0:
            rating_dict['difficulty'] = 0
        else:
            rating_dict['difficulty'] = round(difficulty_total / difficulty_count, 2)
        if replayability_count == 0:
            rating_dict['replayability'] = 0
        else:
            rating_dict['replayability'] = round(replayability_total / replayability_count, 2)
        if graphics_count == 0:
            rating_dict['graphics'] = 0
        else:
            rating_dict['graphics'] = round(graphics_total / graphics_count, 2)
        if audio_count == 0:
            rating_dict['audio'] = 0
        else:
            rating_dict['audio'] = round(audio_total / audio_count, 2)
        if story_count == 0:
            rating_dict['story'] = 0
        else:
            rating_dict['story'] = round(story_total / story_count, 2)
        if recommendability_count == 0:
            rating_dict['recommendability'] = 0
        else:
            rating_dict['recommendability'] = round(recommendability_total / recommendability_count, 2)
        return render(request, 'games/game_detail.html', {'game': game, 'pending_tags':pending_tags, 'user_score':user_score, 'users_rated':users_rated, 'user_counts':user_counts, 'game_entry': game_entry, 'aspect_ratings': rating_dict, 'personal_rating': personal_rating, 'stubbed':stubbed, 'ignored':ignored, 'tab':tab})
    # Tab does not exist
    else:
        raise Http404

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
        collection_list = Collection.objects.filter(Q(name__icontains=query)).prefetch_related('games').prefetch_related('category').order_by('-id')
    else:
        collection_list = Collection.objects.prefetch_related('games').prefetch_related('category').order_by('-id')
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
        user_list = User.objects.filter(Q(name__icontains=query)).prefetch_related('userprofile').order_by('-id')
    else:
        user_list = User.objects.prefetch_related('userprofile').order_by('-id')
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
    if 'next' in request.GET.keys():
        next_url = request.GET['next']
    elif 'next' in request.POST.keys():
        next_url = request.POST['next']
    else:
        next_url = None
    # Viewing list
    if edit_type is None:
        game_list = UserGameListEntry.objects.filter(user=user_id).prefetch_related('platform').prefetch_related('game')
        manual_list = ManualUserGameListEntry.objects.filter(user=user_id).prefetch_related('platform')
        total_list = {"Playing": {}, "Completed": {}, "Paused": {}, "Dropped": {}, "Plan to Play": {}, "Imported": {}}
        for entry in game_list:
            total_list[status_conversion[entry.status]][entry.game.name] = {'id': entry.game.id, 'game_id': entry.game.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed, 'edit_type': 'edit', 'delete_type': 'delete'}
        for entry in manual_list:
            total_list[status_conversion[entry.status]][entry.name] = {'id': entry.id, 'platform': entry.platform, 'score': entry.score, 'hours': entry.hours, 'comments': entry.comments, 'times_replayed': entry.times_replayed, 'edit_type': 'edit-manual', 'delete_type': 'delete-manual', 'never_migrate':entry.never_migrate}
        # Sort dicts
        for status in total_list.keys():
            # TODO: Find a more elegant way to sort one key reversed and the other normally
            sortingmethod = request.GET.get('sort')
            if sortingmethod and sortingmethod in ['score', 'platform', 'hours']:
                templist = []
                for x in total_list[status].keys():
                    if sortingmethod == 'score':
                        templist.append((Decimal(11) if total_list[status][x]['score'] is None else 10 - total_list[status][x]['score'], x, total_list[status][x]))
                    if sortingmethod == 'platform':
                        if total_list[status][x]['platform'] is None:
                            platform = 'None'
                        else:
                            if total_list[status][x]['platform'].shorthand:
                                platform = total_list[status][x]['platform'].shorthand
                            else:
                                platform = total_list[status][x]['platform'].name
                        templist.append((platform, x, total_list[status][x]))
                    if sortingmethod == 'hours':
                        templist.append((10000000000 if total_list[status][x]['hours'] is None else 10000000000 - total_list[status][x]['hours'], x, total_list[status][x]))
                templist.sort()
                total_list[status].clear()
                for x in templist:
                    total_list[status][x[1]] = x[2]
            else:
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
        dropdown_platforms = [x for x in request.user.userprofile.enabled_platforms.all()]
        if game_entry.platform not in dropdown_platforms and game_entry.platform is not None:
            dropdown_platforms = [game_entry.platform] + dropdown_platforms
        return render(request, 'games/edit_manual_game.html', {'form': form, 'game_entry': game_entry, 'dropdown_platforms': dropdown_platforms})
    elif edit_type == 'edit':
        rec = None
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
        custom_lists = CustomList.objects.filter(user=request.user).order_by('name')
        lists_used = [c.id for c in CustomList.objects.filter(user=request.user, games=game)]
        dropdown_platforms = [x for x in request.user.userprofile.enabled_platforms.all()]
        if game_entry.platform not in dropdown_platforms and game_entry.platform is not None:
            dropdown_platforms = [game_entry.platform] + dropdown_platforms
        if request.method == 'POST':
            if game in request.user.userprofile.ignored_games.all():
                request.user.userprofile.ignored_games.remove(game)
            try:
                rec = Recommendation.objects.filter(user=request.user, game=game)
            except Recommendation.DoesNotExist:
                pass
            # create a form instance and populate it with data from the request:
            form = GameEntryForm(request.POST)
            # check whether it's valid
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
                # Update custom lists
                posted_custom_lists = set([int(x) for x in request.POST.getlist('custom_lists')])
                lists_to_add = list(posted_custom_lists - set(lists_used))
                lists_to_remove = list(set(lists_used) - posted_custom_lists)
                # Delete anything that has been unchecked
                for clist in CustomList.objects.filter(user=request.user, id__in=lists_to_remove):
                    clist.games.remove(game)
                # Add anything that has been checked
                for clist in CustomList.objects.filter(user=request.user, id__in=lists_to_add):
                    clist.games.add(game)
                if next_url is not None and next_url.startswith('/') and is_safe_url(next_url, None):
                    return HttpResponseRedirect(next_url)
                else:
                    return HttpResponseRedirect('/game/' + str(game.id))
        else:
            form = ManualGameForm()
        return render(request, 'games/edit_game_entry.html', {'form': form, 'game_id': entry_id, 'game_entry': game_entry, 'custom_lists': custom_lists, 'lists_used': lists_used, 'next': next_url, 'dropdown_platforms': dropdown_platforms})
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
        dropdown_platforms = [x for x in request.user.userprofile.enabled_platforms.all()]
        return render(request, 'games/add_manual_game.html', {'form': form, 'dropdown_platforms': dropdown_platforms})
    else:
        raise Http404

@login_required(login_url='/login/')
def GameListExportView(request):
    status_conversion = {
        "PLAY":"Playing",
        "CMPL":"Completed",
        "HOLD":"Paused",
        "DROP":"Dropped",
        "PLAN":"Plan to Play",
        "IMPT": "Imported"
    }
    user_id = request.user.id
    game_list = UserGameListEntry.objects.filter(user=user_id).prefetch_related('platform').prefetch_related('game')
    manual_list = ManualUserGameListEntry.objects.filter(user=user_id).prefetch_related('platform')
    total_list = []
    for entry in game_list:
        total_list.append({'name': entry.game.name, 'status':status_conversion[entry.status], 'platform': (None if entry.platform is None else entry.platform.name), 'score': (None if entry.score is None else str(entry.score)), 'hours': (None if entry.hours is None else str(entry.hours)), 'comments': entry.comments, 'start_date': (None if entry.start_date is None else str(entry.start_date)), 'stop_date': (None if entry.stop_date is None else str(entry.stop_date)), 'times_replayed': entry.times_replayed})
    for entry in manual_list:
        total_list.append({'name': entry.name, 'status':status_conversion[entry.status], 'platform': (None if entry.platform is None else entry.platform.name), 'score': (None if entry.score is None else str(entry.score)), 'hours': (None if entry.hours is None else str(entry.hours)), 'comments': entry.comments, 'start_date': (None if entry.start_date is None else str(entry.start_date)), 'stop_date': (None if entry.stop_date is None else str(entry.stop_date)), 'times_replayed': entry.times_replayed})
    return HttpResponse(json.dumps(total_list), content_type='application/json')

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
def RateAspectView(request):
    valid_aspects = ['difficulty', 'replayability', 'graphics', 'audio', 'story', 'recommendability']
    game_id = request.GET.get('game')
    aspect = request.GET.get('aspect')
    rating = request.GET.get('rating')
    # Handle invalid games
    if not game_id:
        return render(request, 'games/error_message.html', {'error':'No game ID given!'})
    try:
        game = Game.objects.get(id=game_id)
    except Game.DoesNotExist:
        return render(request, 'games/error_message.html', {'error':'No such game!'})
    # Handle invalid aspects
    if not aspect or aspect not in valid_aspects:
        return render(request, 'games/error_message.html', {'error':'Invalid aspect!'})
    # Handle invalid ratings
    try:
        rating = int(rating)
    except:
        return render(request, 'games/error_message.html', {'error':'Invalid rating!'})
    if rating not in [0, 1, 2, 3, 4, 5]:
        return render(request, 'games/error_message.html', {'error':'Invalid rating!'})

    try:
        user_rating = UserGameAspectRating.objects.get(user=request.user, game=game)
    except UserGameAspectRating.DoesNotExist:
        user_rating = UserGameAspectRating()
        user_rating.user = request.user
        user_rating.game = game
    if aspect == 'difficulty':
        user_rating.difficulty = rating
    elif aspect == 'replayability':
        user_rating.replayability = rating
    elif aspect == 'graphics':
        user_rating.graphics = rating
    elif aspect == 'audio':
        user_rating.audio = rating
    elif aspect == 'story':
        user_rating.story = rating
    elif aspect == 'recommendability':
        user_rating.recommendability = rating
    user_rating.save()
    return redirect('/game/%s/_/aspects' % game.id)

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
def HidePlatformsView(request):
    user_profile = UserProfile.objects.get(user=request.user)
    enabled_platforms = [x.id for x in user_profile.enabled_platforms.all()]
    form = HidePlatformsForm(instance=user_profile)
    if request.method == 'POST':
        form = HidePlatformsForm(request.POST, instance=user_profile)
        print(form.is_valid())
        if form.is_valid():
            form.save()
            return redirect('/settings')
    platforms = {}
    for platform in Platform.objects.all():
        if platform.category in platforms.keys():
            platforms[platform.category].append({'id':platform.id, 'name':platform.name})
        else:
            platforms[platform.category] = [{'id':platform.id, 'name':platform.name}]
    platform_categories = sorted(platforms.keys())
    return render(request, 'games/change_hidden_platforms.html', {'platforms':platforms, 'platform_categories':platform_categories, 'enabled_platforms':enabled_platforms, 'form':form})

@login_required(login_url='/login/')
def ChangeCustomListsView(request):
    lists = CustomList.objects.filter(user=request.user.id).order_by('name')
    if request.method == 'POST':
        pass
    return render(request, 'games/change_custom_lists.html', {'lists':lists})

@login_required(login_url='/login/')
def AddCustomListView(request):
    form = CustomListForm()
    if request.method == 'POST':
        form = CustomListForm(request.POST)
        if form.is_valid():
            tagreq = CustomList()
            tagreq.user = request.user
            tagreq.name = form.cleaned_data['name']
            tagreq.privacy_level = form.cleaned_data['privacy_level']
            tagreq.save()
            return redirect('/settings/customlists/')
    return render(request, 'games/add_custom_list.html', {'form':form})

@login_required(login_url='/login/')
def EditCustomListView(request, list_id):
    try:
        clist = CustomList.objects.get(id=list_id, user=request.user)
    except CustomList.DoesNotExist:
        raise Http404
    form = CustomListForm(instance=clist)
    if request.method == 'POST':
        form = CustomListForm(request.POST)
        if form.is_valid():
            clist.name = form.cleaned_data['name']
            clist.privacy_level = form.cleaned_data['privacy_level']
            clist.save()
            return redirect('/settings/customlists/')
    return render(request, 'games/edit_custom_list.html', {'form':form, 'clist_id':clist.id})

@login_required(login_url='/login/')
def DeleteCustomListView(request, list_id):
    try:
        clist = CustomList.objects.get(id=list_id, user=request.user)
    except CustomList.DoesNotExist:
        raise Http404
    if request.method == 'POST':
        clist.delete()
        return HttpResponseRedirect('/settings/customlists/')
    return render(request, 'games/delete_custom_list.html', {'list_id':list_id, 'name':clist.name})

@login_required(login_url='/login/')
def DeleteStatusView(request, status_id):
    try:
        activitystatus = UserGameStatus.objects.prefetch_related('game').get(id=status_id, user=request.user)
    except UserGameStatus.DoesNotExist:
        raise Http404
    if request.method == 'POST':
        activitystatus.delete()
        return HttpResponseRedirect('/')
    return render(request, 'games/delete_status.html', {'status_id':status_id, 'name':activitystatus.game.name})

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