from .models import Notifications

def unread_notifications_count(request):
    if request.user.is_authenticated:
        unread_count = Notifications.unread_count(request.user)
    else:
        unread_count = 0
    return {'unread_count': unread_count}
