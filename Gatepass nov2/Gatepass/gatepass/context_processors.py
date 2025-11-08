from .models import Notification


def notifications_context(request):
    """Add notifications to global template context"""
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:12]
        return {'notifications': notifications}
    return {'notifications': []}

