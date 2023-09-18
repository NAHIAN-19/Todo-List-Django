from django.contrib.auth.models import User, AbstractUser
from django.db import models
from django.utils import timezone


class Task(models.Model):
    taskTitle = models.CharField(max_length=100)
    category = models.ForeignKey('Category',related_name='tasks', on_delete=models.CASCADE , null=True)
    dueDate = models.DateTimeField()
    completed = models.BooleanField(default=False)
    completedDate = models.DateTimeField(null=True, blank=True)
    createdDate = models.DateTimeField(default=timezone.now())
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    important =models.BooleanField(default=False)

    def __str__(self):
        return self.taskTitle

class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name

class CompletedTask(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.task.taskTitle

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures', default='profile_pictures\default.jpg')
    completed_tasks_count = models.PositiveIntegerField(default=0)

    def update_completed_tasks_count(self):
        self.completed_tasks_count = self.user.task_set.filter(completed=True).count()
        self.save()

    def __str__(self):
        return self.user.username
    
class Solve(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
