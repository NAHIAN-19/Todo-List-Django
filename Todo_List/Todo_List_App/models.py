from django.contrib.auth.models import AbstractUser , User
from django.db import models
from django.utils import timezone
from django.conf import settings
import os
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone = models.CharField(max_length=15)
    address = models.CharField(max_length=100)

    class Meta:
        db_table = "_UserDetails"

    def __str__(self):
        return self.username
class Task(models.Model):
    taskTitle = models.CharField(max_length=200)
    category = models.ForeignKey('Category', related_name='tasks', on_delete=models.CASCADE, null=True)
    dueDate = models.DateTimeField()
    completedDate = models.DateTimeField(null=True, blank=True)
    createdDate = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    important = models.BooleanField(default=False)
    status = models.CharField(max_length=100, default='Pending')
    class Meta:
        db_table = "_TaskDetails"

    def __str__(self):
        return self.taskTitle

class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = "_CategoryDetails"

    def __str__(self):
        return self.name

class CompletedTask(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = "u_Task"

    def __str__(self):
        return self.task.taskTitle

def profile_picture_path(instance, filename):
    return os.path.join('profile_pictures', str(instance.user.id), filename)

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to=profile_picture_path, default='profile_pictures/default.jpg')
    completed_tasks_count = models.PositiveIntegerField(default=0)
    first_name = models.CharField(max_length=30, blank=True)  
    last_name = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=100, blank=True) 

    class Meta:
        db_table = "_ProfileDetails"

    def update_completed_tasks_count(self):
        self.completed_tasks_count = self.user.task_set.filter(status = 'Comepleted').count()
        self.save()

    def __str__(self):
        return self.user.username

class Solve(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()

    class Meta:
        db_table = "user_Details"

class Activity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    task_created = models.PositiveIntegerField(default=0)
    task_edited = models.PositiveIntegerField(default=0)
    task_completed = models.PositiveIntegerField(default=0)
    task_deleted = models.PositiveIntegerField(default=0)
    account_created = models.DateTimeField(auto_now_add=True)
    last_online = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "_Overview"

    def increment_task_created(self):
        self.task_created += 1
        self.save()

    def increment_task_edited(self):
        self.task_edited += 1
        self.save()

    def increment_task_completed(self):
        self.task_completed += 1
        self.save()

    def increment_task_deleted(self):
        self.task_deleted += 1
        self.save()

    def update_last_online(self):
        self.last_online = timezone.now()
        self.save()

    def update_account_created(self):
        self.account_created = timezone.now()
        self.save()

