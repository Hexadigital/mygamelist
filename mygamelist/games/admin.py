from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import ManyToManyField
from django.forms import CheckboxSelectMultiple

# Register your models here.
from .models import Game, Genre, Platform, Tag, UserProfile, UserGameListEntry, ManualUserGameListEntry, GameVerifiedPlatform
from .models import UserGameStatus, Collection, CollectionType, TagAdditionRequest, CustomList, UserGameAspectRating

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

class GameAdmin(admin.ModelAdmin):
    formfield_overrides = {
        ManyToManyField: {'widget': CheckboxSelectMultiple},
    }

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Game, GameAdmin)
admin.site.register(Genre)
admin.site.register(Platform)
admin.site.register(Tag)
admin.site.register(UserGameListEntry)
admin.site.register(ManualUserGameListEntry)
admin.site.register(UserGameStatus)
admin.site.register(Collection)
admin.site.register(CollectionType)
admin.site.register(TagAdditionRequest)
admin.site.register(CustomList)
admin.site.register(UserGameAspectRating)
admin.site.register(GameVerifiedPlatform)