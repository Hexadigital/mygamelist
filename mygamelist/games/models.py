from django.db import models
from decimal import Decimal
from uuid import uuid4
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save

def random_cover_filename(instance, filename):
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid4().hex, ext)
    return 'covers/' + filename

def random_screen_filename(instance, filename):
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid4().hex, ext)
    return 'screenshots/' + filename

def random_avatar_filename(instance, filename):
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid4().hex, ext)
    return 'avatars/' + filename

class Platform(models.Model):
    name = models.CharField(max_length=50)
    category = models.CharField(max_length=50)
    shorthand = models.CharField(max_length=50, blank=True, default='')

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.category + " - " + self.name

class Tag(models.Model):
    name = models.CharField(max_length=50)
    category = models.CharField(max_length=50)
    description = models.CharField(max_length=250, blank=True)
    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.category + " - " + self.name

class Genre(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name

class Game(models.Model):
    name = models.CharField(max_length=150)
    year = models.IntegerField()
    trailer_link = models.URLField(max_length=250, blank=True, default='')
    image = models.ImageField(upload_to=random_cover_filename, null=True)
    screen1 = models.ImageField(upload_to=random_screen_filename, null=True, blank=True)
    screen2 = models.ImageField(upload_to=random_screen_filename, null=True, blank=True)
    screen3 = models.ImageField(upload_to=random_screen_filename, null=True, blank=True)
    screen4 = models.ImageField(upload_to=random_screen_filename, null=True, blank=True)
    genres = models.ManyToManyField(Genre, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    description = models.TextField(blank=True, default='')
    aliases = models.TextField(blank=True, default='')
    main_link = models.URLField(max_length=250, blank=True, default='', verbose_name="Main Website")
    wikipedia_link = models.URLField(max_length=250, blank=True, default='', verbose_name="Wikipedia")
    gamefaqs_link = models.URLField(max_length=250, blank=True, default='', verbose_name="GameFAQs Link")
    steam_link = models.URLField(max_length=250, blank=True, default='', verbose_name="Steam Link")
    howlongtobeat_link = models.URLField(max_length=250, blank=True, default='', verbose_name="HowLongToBeat Link")
    pcgamingwiki_link = models.URLField(max_length=250, blank=True, default='', verbose_name="PCGamingWiki Link")
    winehq_link = models.URLField(max_length=250, blank=True, default='', verbose_name="WineHQ Link")
    mobygames_link = models.URLField(max_length=250, blank=True, default='', verbose_name="MobyGames Link")
    vndb_link = models.URLField(max_length=250, blank=True, default='', verbose_name="VNDB Link")
    temp_pop_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.name + " (" + str(self.year) + ")"

@receiver(post_save, sender=User)
def create_userprofile_signal(sender, instance, created, **kwargs):
    if created:     
        UserProfile.objects.create(user=instance)
        sexual_content = Tag.objects.get(name="Sexual Content")
        stub = Tag.objects.get(name="STUB")
        instance.userprofile.banned_tags.add(sexual_content)
        instance.userprofile.banned_tags.add(stub)
        instance.userprofile.save()

class UserGameListEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    statuses = [
        ("PLAN", "Plan to Play"),
        ("PLAY", "Playing"),
        ("CMPL", "Completed"),
        ("DROP", "Dropped"),
        ("HOLD", "Paused"),
        ("IMPT", "Imported")
    ]
    status = models.CharField(max_length=4, choices=statuses, default="PLAN")
    score = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    hours = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    comments = models.CharField(max_length=500, blank=True, default='')
    start_date = models.DateField(blank=True, null=True)
    stop_date = models.DateField(blank=True, null=True)
    times_replayed = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username + " - " + self.game.name

class ManualUserGameListEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    statuses = [
        ("PLAY", "Playing"),
        ("CMPL", "Completed"),
        ("DROP", "Dropped"),
        ("HOLD", "Paused"),
        ("PLAN", "Plan to Play"),
        ("IMPT", "Imported")
    ]
    status = models.CharField(max_length=4, choices=statuses, default="PLAN")
    score = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    hours = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    comments = models.CharField(max_length=500, blank=True, default='')
    start_date = models.DateField(blank=True, null=True)
    stop_date = models.DateField(blank=True, null=True)
    times_replayed = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username + " - " + self.name

class UserGameStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    statuses = [
        ("PLAY", "Playing"),
        ("CMPL", "Completed"),
        ("DROP", "Dropped"),
        ("HOLD", "Paused"),
        ("PLAN", "Plan to Play")
    ]
    status = models.CharField(max_length=4, choices=statuses)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + " " + self.status + " " + self.game.name

class Notification(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notif_type = models.CharField(max_length=10)
    notif_object_id = models.IntegerField()

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    slot = models.IntegerField()
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    rec_data = models.CharField(max_length=10)

class CollectionType(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name

class Collection(models.Model):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(CollectionType, on_delete=models.CASCADE)
    description = models.TextField(blank=True, default='')
    games = models.ManyToManyField(Game, blank=True)

    def __str__(self):
        return self.category.name + " - " + self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to=random_avatar_filename, default='avatars/default.png')
    banned_tags = models.ManyToManyField(Tag, blank=True)
    ignored_games = models.ManyToManyField(Game, blank=True)
    ignored_collections = models.ManyToManyField(Collection, blank=True)
    followed_users = models.ManyToManyField(User, blank=True, related_name='userprofile_followed_users')

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating_systems = [
        ("SMIL","3-Point Smiley"),
        ("STAR","5-Point Star"),
        ("DECM","10-Point Decimal")
    ]
    score_type = models.CharField(max_length=4, choices=rating_systems, default="DECM")