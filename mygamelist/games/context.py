from .models import Notification

def notification_context_processor(request):
	if request.user.is_authenticated:
		notifs = Notification.objects.filter(user = request.user).count()
		if notifs > 0:
			return {'alert': True}
	return {'alert': False}