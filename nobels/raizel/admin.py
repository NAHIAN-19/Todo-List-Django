from django.contrib import admin
from raizel.models import Task, Category, Profile

class TaskAdmin(admin.ModelAdmin):
    list_display = ('taskTitle', 'category', 'dueDate', 'completed')
    ordering = ('completed', 'dueDate',)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_picture', 'completed_tasks_count')


admin.site.register(Category)
admin.site.register(Task, TaskAdmin)
admin.site.register(Profile, ProfileAdmin)