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
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.username
    
class Task(models.Model):
    taskTitle = models.CharField(max_length=200)
    description = models.TextField(null = True, blank = True)
    category = models.ForeignKey('Category', related_name='tasks', on_delete=models.CASCADE, null=True)
    dueDate = models.DateTimeField(db_column = 'duedate')
    completedDate = models.DateTimeField(null=True, blank=True)
    createdDate = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    important = models.BooleanField(default=False)
    status = models.CharField(max_length=100, default='Pending')
        
    def __str__(self):
        return self.taskTitle

class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name

class CompletedTask(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

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


    def update_completed_tasks_count(self):
        self.completed_tasks_count = self.user.task_set.filter(completed=True).count()
        self.save()

    def __str__(self):
        return self.user.username

class Solve(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()

