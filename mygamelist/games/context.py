from .models import Notification, UserSettings

def notification_context_processor(request):
	if request.user.is_authenticated:
		notifs = Notification.objects.filter(user = request.user).count()
		if notifs > 0:
			return {'alert': True}
	return {'alert': False}

def usersettings_context_processor(request):
	if request.user.is_authenticated:
		try:
			settings = UserSettings.objects.get(user = request.user)
			return {'settings': settings}
		except UserSettings.DoesNotExist:
			pass
	return {}