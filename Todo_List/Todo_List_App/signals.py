from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Notifications, Category, Profile
from django.conf import settings
User = get_user_model()

@receiver(post_save, sender=Notifications)
def update_notifications_count(sender, instance, **kwargs):
    user = instance.user
    user.notificationsCount = Notifications.unread_count(user)
    user.save()
    
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_default_category(sender, instance, created, **kwargs):
    if created:
        Category.objects.get_or_create(name='Others', user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)