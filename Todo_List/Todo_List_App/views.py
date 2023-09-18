from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth import (authenticate, login, logout,
                                update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import (AuthenticationForm, PasswordChangeForm)
from django.db.models import F, Q
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from Todo_List_App.models import Category, Task, Profile
from .forms import PasswordChangeForm, ProfileForm, SignUpForm, SolveForm, CustomSetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm 
from django.contrib.auth import get_user_model

#######################this fucntion is used to signup
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = Profile.objects.create(user=user)
            profile_form = ProfileForm(request.POST, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
            login(request, user)
            messages.success(request, 'Your account has been created successfully!',extra_tags='success')
            return redirect('signin')
    else:
        form = SignUpForm()

    return render(request, 'Sign_up.html', {'form': form})

#######################this function is used for signin
def signin(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if remember_me:
                    request.session.set_expiry(timedelta(days=7).total_seconds())
                else:
                    request.session.set_expiry(0)

                return redirect('todo')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    context = {'form': form}
    return render(request, 'Sign_in.html', context)

#######################this function is used for signout
@login_required
def logout_view(request):
    logout(request)
    return redirect('signin')

#######################this function is used for reseting password
def forgot_password(request):
    request.session['error'] = False
    if request.method == 'POST':
        solve_form = SolveForm(request.POST)
        if solve_form.is_valid():
            username = solve_form.cleaned_data['username']
            email = solve_form.cleaned_data['email']
            try:
                user = User.objects.get(username=username, email=email)
            except User.DoesNotExist:
                user = None
            if user:
                request.session['error'] = False
                request.session['password_reset_verified'] = True
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                request.session['password_reset_timestamp'] = timestamp
                return redirect('reset_password', user_id=user.id)
            else:
                request.session['error'] = True
    if request.session.get('error', True):
        messages.error(request, 'No user with this username and email exists.',extra_tags='error')
    solve_form = SolveForm()
    return render(request, 'forgot_password.html', {'solve_form': solve_form})

#######################this function is redirected from forgot password function
def reset_password(request, user_id):
    if not request.session.get('password_reset_verified', False):
        return redirect('forgot_password')

    timestamp_str = request.session.get('password_reset_timestamp')
    
    if timestamp_str:
        timeout_duration = timedelta(minutes=2)
        current_time = datetime.now()
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
        
        if current_time - timestamp > timeout_duration:
            request.session['password_reset_verified'] = False
            messages.error(request, 'Password reset verification has expired.',extra_tags='error')
            return redirect('forgot_password')
    
    try:
        user_id = int(user_id)
        user = User.objects.get(pk=user_id)
    except (ValueError, User.DoesNotExist):
        raise Http404("No such user")
    
    if request.method == 'POST':
        form = CustomSetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            request.session.pop('password_reset_verified', None)
            request.session.pop('password_reset_timestamp', None)
            messages.success(request, 'Password reset successful. You can now log in with your new password.',extra_tags='success')
            return redirect('signin')
        else:
            messages.error(request, 'Invalid password , please try again.',extra_tags='error')
    else:
        form = CustomSetPasswordForm(user) 

    context = {'form': form, 'user_id': user_id}
    return render(request, 'reset_password.html', context)

#######################this function shows and edit information of that user
@login_required
def profile(request):
    user = request.user
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        profile = Profile(user=user)
        profile.save()

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        password_form = PasswordChangeForm(user, request.POST)

        if form.is_valid():
            if request.POST['change_password'] == 'change':
                if password_form.is_valid():
                    password_form.save()
                    update_session_auth_hash(request, user) 

            user.email = request.POST['email']
            user.save()
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
        password_form = PasswordChangeForm(user)

    context = {'form': form, 'password_form': password_form}
    return render(request, 'profile.html', context)

#######################this function is used for ADDING task for that user
@login_required
def Todo_List_App(request):
    categories = Category.objects.filter(user=request.user)
    context = {'categories': categories, 'success': False}

    if request.method == "POST":
        title = request.POST['title']
        category_id = request.POST['category']
        category = Category.objects.get(id=category_id)
        due_date = request.POST['due_date']
        due_time = request.POST['dueTime']
        important = request.POST.get('important')

        due_datetime = datetime.strptime(f"{due_date} {due_time}", '%Y-%m-%d %H:%M')
        min_due_datetime = timezone.now() + timedelta(minutes=5)
        due_datetime = timezone.make_aware(due_datetime, timezone.get_current_timezone())

        if due_datetime <= min_due_datetime:
            messages.error(request, f"Due datetime must be at least 5 minutes from now. You entered {due_datetime.strftime('%Y-%m-%d |  %H:%M')}.")
            due_datetime = timezone.now() + timedelta(minutes=5)

        task = Task(
            taskTitle=title,
            category=category,
            dueDate=due_datetime,
            user=request.user,
            important = bool(important),
        )
        task.save()
        context['success'] = True

    if not categories:
        context['no_categories'] = True

    running_tasks = Task.objects.filter(completed=False)
    context['running_tasks'] = running_tasks
    return render(request, 'index.html', context)

#######################this function shows all the running tasks of that user
@login_required
def running_tasks(request):
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', '')
    tasks = Task.objects.filter(user=request.user,completed=False)
    tasks = tasks.order_by(F('important').desc())
    if sort_by == 'asc':
        tasks = tasks.order_by('dueDate')
    elif sort_by == 'desc':
        tasks = tasks.order_by(F('dueDate').desc())
        
    is_refreshed = request.GET.get('refresh', False)
    task_count = tasks.count()
    if not is_refreshed:
        if search_query:
            tasks = tasks.filter(taskTitle__icontains=search_query)
            task_count = tasks.count()
        if not task_count and search_query:
            messages.warning(request, f'Task "{search_query}" wasn\'t found.')
        elif task_count and search_query:
            messages.success(request, f'[{task_count}] tasks found matching your search query.')
        elif not task_count and not search_query:
            messages.warning(request, 'Running Task list is empty.')
    context = {
        'tasks': tasks,
        'search_query': search_query,
    }
    return render(request, 'tasks.html', context)

#######################this function edits the specific running task of that user
@login_required  
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)

    categories = Category.objects.all()

    if request.method == "POST":
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        category = get_object_or_404(Category, id=category_id)
        important = request.POST.get('important')
        if category is None:
            return HttpResponse("Category not found", status=404)

        due_date = request.POST.get('due_date')
        due_time = request.POST.get('dueTime')

        due_datetime = datetime.strptime(f"{due_date} {due_time}", '%Y-%m-%d %H:%M')
        min_due_datetime = timezone.now() + timedelta(minutes=5)
        due_datetime = timezone.make_aware(due_datetime, timezone.get_current_timezone())

        if due_datetime <= min_due_datetime:
            due_datetime = timezone.now() + timedelta(minutes=5)

        task.taskTitle = title
        task.category = category
        task.dueDate = due_datetime
        task.important = bool(important)
        task.save()

        messages.success(request, "Task updated successfully!")

        return redirect('running_tasks') 

    context = {'task': task, 'categories': categories}
    return render(request, 'edit.html', context)

#######################this fucntion is used for completing tasks 
@require_POST
def mark_task_completed(request, task_id):
    task = get_object_or_404(Task, id=task_id,user=request.user)
    task.completed = True
    task.completedDate = timezone.now()
    task.save()

    profile = Profile.objects.get(user=request.user)
    profile.completed_tasks_count += 1
    profile.save()

    messages.success(request, f'Task "{task.taskTitle}" marked as completed successfully. It has been moved to the''Completed Tasks' 'tab.')
    return redirect('running_tasks')

#######################this function deletes that specific task details from running tasks of that user
@login_required 
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    messages.success(request, f'Task "{task.taskTitle}" has been deleted successfully.')
    return redirect('running_tasks')

#######################this fucntion shows the completed tasks of that user
@login_required
def completed_tasks(request):
    sort_by = request.GET.get('sort_by', '')
    search_query = request.GET.get('search', '')
    completed_tasks = Task.objects.filter(user=request.user, completed=True)
    if sort_by == 'asc':
        completed_tasks = completed_tasks.order_by('dueDate')
    elif sort_by == 'desc':
        completed_tasks = completed_tasks.order_by(F('dueDate').desc())
        
    is_refreshed = request.GET.get('refresh', False)
    
    if not is_refreshed:
        if search_query:
            completed_tasks = completed_tasks.filter(taskTitle__icontains=search_query)
        task_count = completed_tasks.count()
        if not task_count and search_query:
            messages.warning(request, f'Task "{search_query}" wasn\'t found.')
        elif task_count and search_query:
            messages.success(request, f'[{task_count}] tasks found matching your search query.')
        elif not task_count and not search_query:
            messages.warning(request, 'You haven\'t completed any tasks yet.')
    context = {
        'completed_tasks': completed_tasks,
        'search_query': search_query,
    }
    return render(request, 'completed.html', context)

#######################this function clears all those completed task details of that user
@login_required
def clear_history(request):
    Task.objects.filter(Q(completed=True),user=request.user).delete()
    messages.success(request, 'Completed tasks history has been cleared.')
    return redirect('completed_tasks')

#######################this function adds a category for that user
@login_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST['name']
        existing_category = Category.objects.filter(name=name, user=request.user).first()
        if existing_category:
            messages.error(request, 'Category with the same name already exists.')
        else:
            category = Category(name=name, user=request.user)
            category.save()
            messages.success(request, 'Category added successfully!')
    categories = Category.objects.filter(user=request.user)
    context = {'categories': categories}
    return render(request, 'add_category.html', context)

#######################this function is used to show the categories and all those tasks that the user has
@login_required
def all_categories(request, category_id=None):
    categories = Category.objects.filter(user=request.user)
    categories = categories.order_by('name')
    tasks = Task.objects.all()

    if category_id is not None:
        tasks = tasks.filter(category_id=category_id)
        tasks = tasks.order_by('important')
    context = {
        'categories': categories,
        'tasks': tasks
    }
    if not categories:
        context['no_categories'] = True
    return render(request, 'all_categories.html', context)

#######################this function deletes specific category along with those associated tasks of that user
@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user)
    category.delete()
    return redirect('all_categories')
#######################this function is used to delete user account
@login_required
def delete_account(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        return HttpResponse("<div class=\"container\" align =\"center\"><h1>: ERROR :</h1></div><center><h2><br>Admin accounts can only be deleted from ADMIN page.</h2></center>")
    
    if request.method == 'POST':
        confirm = request.POST.get('confirm', '')
        if confirm == 'CONFIRM':
            user.delete()
            logout(request)
            return redirect('signin')
        else:
            return redirect('profile')
    return render(request, 'sign_in.html', {'user': user})

