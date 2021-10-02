import re
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

def mobile_context_processor(request):
	mobile_regex = re.compile(r".*(iphone|mobile|androidtouch)", re.IGNORECASE)
	if mobile_regex.match(request.META['HTTP_USER_AGENT']):
		return {"mobile": True}
	else:
		return {"mobile": False}