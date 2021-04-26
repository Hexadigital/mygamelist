from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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