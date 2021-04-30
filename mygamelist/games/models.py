from django.db import models
from decimal import Decimal
from uuid import uuid4
from django.contrib.auth.models import User

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
    name = models.CharField(max_length=50)
    year = models.IntegerField()
    magic_number = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    trailer_link = models.URLField(max_length=250, blank=True, default='')
    image = models.ImageField(upload_to=random_cover_filename, null=True)
    screen1 = models.ImageField(upload_to=random_screen_filename, null=True)
    screen2 = models.ImageField(upload_to=random_screen_filename, null=True)
    screen3 = models.ImageField(upload_to=random_screen_filename, null=True)
    screen4 = models.ImageField(upload_to=random_screen_filename, null=True)
    platforms = models.ManyToManyField(Platform, blank=True)
    genres = models.ManyToManyField(Genre, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    description = models.TextField(blank=True, default='')
    main_link = models.URLField(max_length=250, blank=True, default='', verbose_name="Main Website")
    wikipedia_link = models.URLField(max_length=250, blank=True, default='', verbose_name="Wikipedia")
    gamefaqs_link = models.URLField(max_length=250, blank=True, default='', verbose_name="GameFAQs Link")
    steam_link = models.URLField(max_length=250, blank=True, default='', verbose_name="Steam Link")
    howlongtobeat_link = models.URLField(max_length=250, blank=True, default='', verbose_name="HowLongToBeat Link")
    pcgamingwiki_link = models.URLField(max_length=250, blank=True, default='', verbose_name="PCGamingWiki Link")
    winehq_link = models.URLField(max_length=250, blank=True, default='', verbose_name="WineHQ Link")
    mobygames_link = models.URLField(max_length=250, blank=True, default='', verbose_name="MobyGames Link")
    vndb_link = models.URLField(max_length=250, blank=True, default='', verbose_name="VNDB Link")

    def __str__(self):
        return self.name + " (" + str(self.year) + ")"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to=random_avatar_filename, null=True)
    games_added = models.IntegerField(default=0)
    edits_made = models.IntegerField(default=0)