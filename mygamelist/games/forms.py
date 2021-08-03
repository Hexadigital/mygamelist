import magic
from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ManualUserGameListEntry, UserGameListEntry, Platform, UserProfile, Tag

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254)

    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['email'].widget.attrs.update({'placeholder': 'Email'})
            self.fields['username'].widget.attrs.update({'placeholder': 'Username'})
            self.fields['password1'].widget.attrs.update({'placeholder': 'Password'})
            self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm Password'})

    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2', )

class ManualGameForm(forms.ModelForm):
    class Meta:
        model = ManualUserGameListEntry
        fields = ['name', 'platform', 'status', 'score', 'hours', 'comments', 'start_date', 'stop_date', 'times_replayed']
        
        widgets = {
            'start_date': forms.DateInput(format='%Y-%m-%d'),
            'stop_date': forms.DateInput(format='%Y-%m-%d')
        }

class GameEntryForm(forms.ModelForm):
    class Meta:
        model = UserGameListEntry
        fields = ['platform', 'status', 'score', 'hours', 'comments', 'start_date', 'stop_date', 'times_replayed']
        
        widgets = {
            'start_date': forms.DateInput(format='%Y-%m-%d'),
            'stop_date': forms.DateInput(format='%Y-%m-%d')
        }

class ChangeAvatarForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']

    def clean_avatar(self):
        avatar = self.cleaned_data['avatar']

        main, sub = magic.from_buffer(avatar.read(), mime=True).split('/')
        if not (main == 'image' and sub in ['jpeg', 'gif', 'png']):
            raise forms.ValidationError(u'Please use a JPEG, GIF or PNG image.')

        if len(avatar) > (512 * 1024):
            raise forms.ValidationError(u'Avatar file size may not exceed 512KB.')

        return avatar

class ChangeIgnoredTagsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['banned_tags']
    banned_tags = forms.ModelMultipleChoiceField(
            queryset=Tag.objects.all(),
            widget=forms.CheckboxSelectMultiple
        )