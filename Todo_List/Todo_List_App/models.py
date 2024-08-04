from django.contrib.auth.models import AbstractUser , User
from django.db import models
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import os
from django.utils.deconstruct import deconstructible
from .utils import resize_image
from cryptography.fernet import Fernet

def get_fernet_key():
    return settings.FERNET_KEY

fernet = Fernet(get_fernet_key())

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    firstName = models.CharField(max_length=30, default='Name1')
    lastName = models.CharField(max_length=30, default='Name2')
    phone = models.CharField(max_length=15, default='0123456789')
    address = models.CharField(max_length=180, default='Earth')
    email_verified = models.BooleanField(default=False)
    encrypted_id = models.CharField(max_length=256, blank=True, editable=False, unique=True)
    
    def save(self, *args, **kwargs):
        if self.pk is None and not self.encrypted_id:
            super().save(*args, **kwargs)
            self.encrypted_id = fernet.encrypt(str(self.id).encode()).decode()
            super().save(update_fields=['encrypted_id'])
        else:
            super().save(*args, **kwargs)
    
    def __str__(self):
        return self.username
    
    @staticmethod
    def encrypt_id(user_id):
        return fernet.encrypt(str(user_id).encode()).decode()
    
    @staticmethod
    def decrypt_id(encrypted_id):
        return int(fernet.decrypt(encrypted_id.encode()).decode())
    
class PasswordResetRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    reset_link_used = models.BooleanField(default=False)
    reset_link_expiry = models.DateTimeField(null=True, blank=True)
    reset_link_generated_at = models.DateTimeField(null=True, blank=True)

    email_verification_limit = models.PositiveIntegerField(default=5) 
    email_verification_timestamp = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def email_verification_limit_reached(user, limit, duration):
        time_threshold = timezone.now() - timedelta(minutes=duration)
        recent_verifications = PasswordResetRequest.objects.filter(
            user=user,
            email_verification_timestamp__gt=time_threshold
        )
        if recent_verifications.count() >= limit:
            first_verification_time = recent_verifications.earliest('email_verification_timestamp').email_verification_timestamp
            remaining_time = duration - int((timezone.now() - first_verification_time).total_seconds() // 60)
            return True, remaining_time
        return False, None
    
    @staticmethod
    def request_limit_reached(user, limit, duration):
        user_id = CustomUser.decrypt_id(user.encrypted_id)
        time_threshold = timezone.now() - timedelta(minutes=duration)
        recent_requests = PasswordResetRequest.objects.filter(user_id=user_id, timestamp__gt=time_threshold)
        if recent_requests.count() >= limit:
            first_request_time = recent_requests.earliest('timestamp').timestamp
            remaining_time = duration - int((timezone.now() - first_request_time).total_seconds() // 60)
            return True, remaining_time
        return False, None

    def save(self, *args, **kwargs):
        if not self.reset_link_expiry:
            self.reset_link_expiry = timezone.now() + timedelta(minutes=20)
        super().save(*args, **kwargs)


class Task(models.Model):
    HIGH = 'High'
    MEDIUM = 'Medium'
    LOW = 'Low'
    PENDING = 'Pending'
    COMPLETED = 'Completed'
    OVERDUE = 'Overdue'
    IMPORTANCE_CHOICES = [
        (HIGH, 'High'),
        (MEDIUM, 'Medium'),
        (LOW, 'Low'),
    ]
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (OVERDUE, 'Overdue'),
    ]
    taskTitle = models.CharField(max_length=100)
    description = models.TextField(null = True, blank = True, max_length=500)
    category = models.ForeignKey('Category', related_name='tasks', on_delete=models.CASCADE, null=True)
    dueDate = models.DateTimeField(db_column = 'duedate')
    completedDate = models.DateTimeField(null=True, blank=True)
    createdDate = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    important = models.CharField(
        max_length=6,
        choices=IMPORTANCE_CHOICES,
        default=LOW,
    )
    status = models.CharField(
        max_length=9,
        choices = STATUS_CHOICES,
        default=PENDING
        )
    notificationTime = models.IntegerField(default=4)
    sent_reminder = models.BooleanField(default=False)
    emailNotification = models.BooleanField(default=False)
    encrypted_id = models.CharField(max_length=256, blank=True, editable=False, unique=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.encrypted_id = fernet.encrypt(str(self.id).encode()).decode()
            super().save(update_fields=['encrypted_id'])

    def __str__(self):
        return self.taskTitle

    @staticmethod
    def decrypt_id(encrypted_id):
        return int(fernet.decrypt(encrypted_id.encode()).decode())

class Category(models.Model):
    name = models.CharField(max_length=50, default='Others')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name
    
    def task_count(self):
        return self.tasks.count()

class CompletedTask(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.task.taskTitle

@deconstructible
class PathAndRename:
    def __init__(self, path):
        self.path = path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        
        username = instance.user.username

        count = instance.profile_picture_change_count
        filename = f'pp_{username}_{count}.{ext}'
        
        return os.path.join(self.path, str(instance.user.id), filename)


class Profile(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('None', 'Rather not say'),
        ('Other', 'Other'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profilePicture = models.ImageField(upload_to=PathAndRename('profile_pictures'), default='default.png')
    profile_picture_change_count = models.PositiveIntegerField(default=0)
    completedTasksCount = models.PositiveIntegerField(default=0)
    enableEmailNotifications = models.BooleanField(default=False)
    bio = models.TextField(max_length=230, blank=True, default='Searching for the meaning of life')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='None')
    
    def update_completed_tasks_count(self):
        self.completedTasksCount = self.user.task_set.filter(completed=True).count()
        self.save()
    # check if old picture is default or another
    # if another , then it will be remove and add the new picture
    # with a custom file name after resizing using PIL
    def save(self, *args, **kwargs):
        if self.pk:
            old_profile = Profile.objects.get(pk=self.pk)
            if old_profile.profilePicture and old_profile.profilePicture.name != self.profilePicture.name:
                if old_profile.profilePicture.name != 'default.png':
                    old_profile.profilePicture.delete(save=False)
                
                self.profile_picture_change_count += 1
                self.profilePicture = resize_image(self.profilePicture)
        else:
            if self.profilePicture:
                self.profilePicture = resize_image(self.profilePicture)
            
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username


class Solve(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()

class Notifications(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200, default='This is a notification')
    date = models.DateTimeField(default=timezone.now)
    unread = models.BooleanField(default=True)
    notificationsCount = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    @classmethod
    def unread_count(cls, user):
        user_id = CustomUser.decrypt_id(user.encrypted_id)
        return cls.objects.filter(user_id=user_id, unread=True).count()