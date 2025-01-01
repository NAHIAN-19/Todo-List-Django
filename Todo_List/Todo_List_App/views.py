import base64
import csv
import json
import threading
import shutil
import time
import os
from datetime import datetime, timedelta
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (authenticate, get_user_model, login, logout,
                                update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.tokens import default_token_generator
from django.core.files.storage import default_storage
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Case, CharField, F, Q, Value, When
from django.http import (Http404, HttpResponse, HttpResponseForbidden,
                        JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from PIL import Image
from Todo_List_App.models import (Category, CustomUser, Notifications,
                                PasswordResetRequest, Profile, Task)
from weasyprint import HTML
from .tasks import send_welcome_email, create_notification
from .forms import (CustomSetPasswordForm, PasswordChangeForm, ProfileForm,
                    SignUpForm)

from_email = settings.EMAIL_HOST_USER
CustomUser = get_user_model()

############## this function changes the status of the task of that user
def update_task_status():
    now = timezone.now()
    tasks_queryset = Task.objects.filter(status=Task.PENDING)
    tasks_queryset = tasks_queryset.annotate(
        task_status=Case(
            When(dueDate__lt=now, then=Value(Task.OVERDUE)),
            default=Value(Task.PENDING),
            output_field=CharField(),
        ),
    )
    for task in tasks_queryset:
        if task.dueDate <= now :
            task.status = Task.OVERDUE
        else:
            task.status = Task.PENDING
        task.save()
#######################this function is used to signup
def signup(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            user.firstName = form.cleaned_data['firstName']
            user.lastName = form.cleaned_data['lastName']
            user.phone = form.cleaned_data['phone']
            user.address = form.cleaned_data['address']
            
            user.save()
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                profile_form = ProfileForm(request.POST,request.FILES, instance=profile, user_instance=user)
                if profile_form.is_valid():
                    profile_form.save()
            login(request, user)
            
            # Trigger background tasks
            send_welcome_email.delay(user.id)  # Pass the user ID to the Celery task
            create_notification.delay(user.id, 'Account Created', timezone.now())

            # Success messages
            messages.success(request, f'Welcome {user.username}', extra_tags='profileInfoSuccess')
            messages.success(request, 'Verify email to receive reminder & reset password', extra_tags='profileInfoSuccess')
            return redirect('profile')
        else:
            messages.error(request, 'Signup failed',extra_tags='authError')
            return render(request, 'authentication.html', {'form': form})
    else:
        form = SignUpForm()

    return render(request, 'authentication.html',{'form': form})
################ Check if the username/email entered in the signup form already exists before submitting the form
def validate_field(request):
    field_type = request.GET.get('type')
    field_value = request.GET.get('value')
    
    if field_type == 'username':
        exists = CustomUser.objects.filter(username=field_value).exists()
    elif field_type == 'email':
        exists = CustomUser.objects.filter(email=field_value).exists()
    else:
        exists = False
    
    return JsonResponse({'exists': exists})

#######################this function is used for signin
def signin(request):
    if request.user.is_authenticated:
        return redirect('home')
    context = {'userPass':False, 'wrongBoth':False}
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        userName = request.POST.get('username')
        context['userName'] = userName
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            user = authenticate(request, username=username, password=password)
            if user is not None:
                notifications = Notifications (
                    name = 'Logged In',
                    date = timezone.now(),
                    user = user,
                )
                notifications.notificationsCount += 1
                notifications.save()
                if user.is_superuser and user.encrypted_id is None:
                    user.encrypted_id = CustomUser.encrypt_id(int(user.id))
                    user.save()
                login(request, user)
                
                if remember_me:
                    request.session.set_expiry(timedelta(days=7).total_seconds())
                else:
                    request.session.set_expiry(0)
                if 'next' in request.POST:
                    return redirect(request.POST.get('next'))
                else:
                    return(redirect('home'))
        else:
            username = form.cleaned_data['username']
            userName = CustomUser.objects.filter(username=userName).first()
            if userName:
                context['wrongPass'] = True
                messages.error(request, 'Incorrect Password',extra_tags='authError')
            else:
                context['wrongBoth'] = True
                messages.error(request, 'Incorrect Username and Password',extra_tags='authError')
            context['form'] = form
            return render(request, 'authentication.html', context)
    else:
        form = AuthenticationForm()
    context = {'form': form}
    return render(request, 'authentication.html', context)

#######################this function is used for signout
@login_required
def logout_view(request):
    logout(request)
    return redirect('signin')

#######################this sends the verification email to the logged in user
def send_verification_email(request, user_id):
    user = get_object_or_404(CustomUser, encrypted_id=user_id)
    
    if user.email_verified:
        messages.info(request, 'Email is already verified.', extra_tags='profileInfoSuccess')
        return redirect('profile')
    
    # Define limit and duration for email verifications
    verification_limit = 5
    verification_duration = 60  # minutes
    
    # Check if email verification limit has been reached
    limit_reached, remaining_time = PasswordResetRequest.email_verification_limit_reached(user, verification_limit, verification_duration)
    if limit_reached:
        if remaining_time is not None:
            messages.error(request, f"Maximum email verification requests reached. Please try again in {remaining_time} minutes.", extra_tags='profileInfoError')
        else:
            messages.error(request, "Maximum email verification requests reached. Please try again later.", extra_tags='profileInfoError')
        return redirect('profile')
    # Create a new email verification request
    reset_request = PasswordResetRequest(
        user=user,
        email_verification_timestamp=timezone.now()
    )
    reset_request.save()
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.encrypted_id))
    verification_link = request.build_absolute_uri(reverse('verify_email')) + f'?uid={uid}&token={token}'
    subject = 'Email Verification'
    message = f"Please click the link below to verify your email address: <a href='{verification_link}'>Verify Email</a>"
    fromEmail = settings.DEFAULT_FROM_EMAIL 
    to_email = user.email
    
    html_content = f"""
        <html>
            <body>
                <p>{message}</p>
            </body>
        </html>
    """
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject,
        text_content,
        fromEmail,
        [to_email],
    )
    email.attach_alternative(html_content, "text/html")
    
    try:
        email.send()
        notifications = Notifications(
            name='Verification Email Sent',
            date=timezone.now(),
            user=user,
        )
        notifications.notificationsCount += 1
        notifications.save()
        messages.success(request, 'Verification email sent successfully! Please check your mail.', extra_tags='profileInfoSuccess')
    except Exception as e:
        errorMessage = str(e)
        notifications = Notifications(
            name=f'Verification Email Sending Failed: {errorMessage}',
            date=timezone.now(),
            user=user,
        )
        notifications.save()
        messages.error(request, 'There was a problem sending the email. Please try again later.', extra_tags='profileInfoError')
    
    return redirect('profile')

###################### this function verifies the email of the logged in user
def verify_email(request):
    uidb64 = request.GET.get('uid')
    token = request.GET.get('token')

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user_id = CustomUser.decrypt_id(uid)
        user = CustomUser.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.email_verified = True
        user.save()
        notifications = Notifications(
            name='Email Verified',
            date=timezone.now(),
            user=user,
        )
        notifications.notificationsCount += 1
        notifications.save()
        messages.success(request, 'Email verification successful.', extra_tags='profileInfoSuccess')
    else:
        if user is not None:
            notifications = Notifications(
                name='Email Verification Failed',
                date=timezone.now(),
                user=user,
            )
            notifications.notificationsCount += 1
            notifications.save()
        messages.error(request, 'Email verification failed.', extra_tags='profileInfoError')

    return redirect('profile')

#######################this function is used to find the account of the user
def findAccount(request):
    try:
        user = request.user
    except:
        user = None
    if user.is_authenticated:
        return redirect('home')
    user = None
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(username=username, email=email)
        except CustomUser.DoesNotExist:
            user = None
        if not user:
            userList = CustomUser.objects.filter(username=username).first()
            messages.error(request, 'User with this Email doesn\'t exist', extra_tags='findAccountError')
            return render(request, 'findAccount.html', {'user': user, 'username': username, 'email': email, 'userName' : userList})
        else:
            return render(request, 'findAccount.html', {'user': user, 'emailVerified': user.email_verified})
    return render(request, 'findAccount.html', {'user': user})

####################### Send reset link to user mail to change password
def sendResetLink(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        user = CustomUser.objects.filter(username=username, email=email).first()

        if user is None:
            messages.error(request, 'User not found.',extra_tags='findAccountError')
            return render(request, 'findAccount.html')

        if not user.email_verified:
            messages.error(request, 'Email is not verified.',extra_tags='resetLinkError')
            return render(request, 'findAccount.html', {'user': user, 'emailVerified': user.email_verified})

        limit = 5
        duration = 60
        limit_reached, remaining_time = PasswordResetRequest.request_limit_reached(user, limit, duration)
        if limit_reached:
            messages.error(request, f"Maximum password reset requests reached. Please try again in {remaining_time} minutes.", extra_tags='resetLinkError')
            return render(request, 'findAccount.html', {'user': user, 'emailVerified': user.email_verified})

        # Mark all previous reset links as used
        PasswordResetRequest.objects.filter(user=user).update(reset_link_used=True, reset_link_generated_at=None, reset_link_expiry=None)

        # Create a new reset request
        reset_request = PasswordResetRequest.objects.create(
            user=user,
            reset_link_used=False,
            reset_link_expiry=timezone.now() + timedelta(minutes=20),
            reset_link_generated_at=timezone.now()
        )
        # Encrypt user ID for the reset link
        encrypted_uid = CustomUser.encrypt_id(user.id)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(encrypted_uid))
        reset_link = request.build_absolute_uri(reverse('checkResetLink')) + f'?uid={uid}&token={token}'
        reset_html = f'<a href="{reset_link}">Reset Password</a>'
        message = f"Please click the link below to reset your password: {reset_html}. This link will expire in 20 minutes. If you didn't request a password reset, please ignore this email."

        subject = 'Password Reset'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = user.email

        html_content = f"""
            <html>
                <body>
                    <p>{message}</p>
                </body>
            </html>
        """
        text_content = strip_tags(html_content)
        email = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            [to_email],
        )
        email.attach_alternative(html_content, "text/html")
        try:
            email.send()
            notifications = Notifications(
                name='Reset Link Sent',
                date=timezone.now(),
                user=user,
            )
            notifications.notificationsCount += 1
            notifications.save()
            reset_request.save()
        except Exception as e:
            errorMessage = str(e)
            if "Connection unexpectedly closed" in errorMessage:
                errorMessage = 'There was a problem connecting to the email server. Please try again later.'
            elif "Authentication" in errorMessage:
                errorMessage = 'Authentication with the email server failed. Please contact support.'
            else:
                errorMessage = 'There was a problem sending the reset link. Please try again later.'
            notifications = Notifications(
                name=f'Reset link sending failed: {errorMessage}',
                date=timezone.now(),
                user=user,
            )
            notifications.notificationsCount += 1
            notifications.save()
            messages.error(request, f'Error: {errorMessage}', extra_tags='resetLinkError')
            return redirect('findAccount')

        messages.success(request, 'Password reset email sent.', extra_tags='resetLinkSuccess')
        return redirect('findAccount')

    return HttpResponseForbidden("Forbidden")

#######################this function is used to check the reset link of the user to reset password
def checkResetLink(request):
    uidb64 = request.GET.get('uid')
    token = request.GET.get('token')
    user = None
    
    try:
        # Decrypt the user ID from the base64 encoded string
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=CustomUser.decrypt_id(uid))
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        try:
            reset_request = PasswordResetRequest.objects.filter(user=user).latest('timestamp')
        except PasswordResetRequest.DoesNotExist:
            reset_request = None
        
        if reset_request is None or reset_request.reset_link_used or reset_request.reset_link_expiry < timezone.now():
            messages.error(request, 'This reset link is invalid or expired.', extra_tags='resetLinkError')
            return redirect('findAccount')
        
        # Set the session flag to indicate that the reset link is verified
        request.session['resetLinkVerified'] = True
        reset_request.reset_link_generated_at = timezone.now()
        reset_request.save()
        
        # Redirect to the password reset view using encrypted user ID
        encrypted_user_id = CustomUser.encrypt_id(user.id)
        return redirect('reset_password', user_id=encrypted_user_id)
    else:
        messages.error(request, 'Invalid password reset link.', extra_tags='resetLinkError')
        return redirect('findAccount')

####################### Removes session value upon clicking Cancel
@csrf_exempt
@require_POST
def invalidate_session(request):
    data = json.loads(request.body)
    user_id = data.get('user_id')
    if not user_id:
        return JsonResponse({'status': 'failed', 'error': 'User ID not provided'})
    
    try:
        decrypted_user_id = CustomUser.decrypt_id(user_id)
        user = get_object_or_404(CustomUser, pk=decrypted_user_id)
        reset_request = PasswordResetRequest.objects.filter(user=user).latest('timestamp')
        
        reset_request.reset_link_used = True
        reset_request.reset_link_expiry = None
        reset_request.reset_link_generated_at = None
        reset_request.save()
        
        request.session.pop('resetLinkVerified', None)
        
        return JsonResponse({'status': 'success'})
    except PasswordResetRequest.DoesNotExist:
        return JsonResponse({'status': 'failed', 'error': 'No password reset request found for this user'})
    except CustomUser.DoesNotExist:
        return JsonResponse({'status': 'failed', 'error': 'User not found'})
    except Exception as e:
        return JsonResponse({'status': 'failed', 'error': str(e)})

#######################this function is redirected from forgot password function to set new passwords
def reset_password(request, user_id):
    if 'resetLinkVerified' not in request.session:
        return redirect('findAccount')
    
    try:
        decrypted_user_id = CustomUser.decrypt_id(user_id)
        user = CustomUser.objects.get(pk=decrypted_user_id)
    except (ValueError, CustomUser.DoesNotExist):
        raise Http404("No such user")
    
    reset_link_duration = timedelta(minutes=20)
    reset_request = PasswordResetRequest.objects.filter(user=user).latest('timestamp')
    expiration_time = reset_request.reset_link_generated_at + reset_link_duration
    remaining_time = (expiration_time - timezone.now()).total_seconds()
    
    if remaining_time <= 0:
        request.session.pop('resetLinkVerified')
        reset_request.reset_link_generated_at = None
        reset_request.reset_link_expiry = None
        reset_request.reset_link_used = True
        reset_request.save()
        messages.error(request, 'Password reset timeout.', extra_tags='resetLinkError')
        return redirect('findAccount')
    
    if request.method == 'POST':
        form = CustomSetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            reset_request.reset_link_used = True
            reset_request.reset_link_expiry = None
            reset_request.save()
            request.session.pop('resetLinkVerified')
            notifications = Notifications(
                name='Password Reset Successful',
                date=timezone.now(),
                user=user,
            )
            notifications.save()
            messages.success(request, 'Password reset successful.', extra_tags='resetPassSuccess')
            
            # Email to user if password reset is successful
            message = f"Your password has been successfully reset. If you didn't request a password reset, please contact support."
            subject = 'Password Reset Successful'
            fromEmail = settings.DEFAULT_FROM_EMAIL
            to_email = user.email

            html_content = f"""
                    <html>
                        <body>
                            <p>{message}</p>
                        </body>
                    </html>
            """
            text_content = strip_tags(html_content)
            email = EmailMultiAlternatives(
                subject,
                text_content,
                fromEmail,
                [to_email],
            )
            email.attach_alternative(html_content, "text/html")
            try:
                email.send()
            except Exception as e:
                errorMessage = str(e)
                if "Connection unexpectedly closed" in errorMessage:
                    errorMessage = 'There was a problem connecting to the email server. Please try again later.'
                elif "Authentication" in errorMessage:
                    errorMessage = 'Authentication with the email server failed. Please contact support.'
                else:
                    errorMessage = 'There was a problem sending the reset link. Please try again later.'
                notifications = Notifications(
                    name=f'Password reset confirmation email sending failed: {errorMessage}',
                    date=timezone.now(),
                    user=user,
                )
                notifications.notificationsCount += 1
                notifications.save()
            return redirect('signin')
        else:
            messages.error(request, 'Password reset failed.', extra_tags='resetPassError')
            return render(request, 'resetPassword.html', {'form': form, 'user_id': user_id, 'remaining_time': int(remaining_time)})
    else:
        form = CustomSetPasswordForm(user=user)
    context = {'form': form, 'user_id': user_id, 'remaining_time': int(remaining_time)}
    return render(request, 'resetPassword.html', context)


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
        form = ProfileForm(request.POST, request.FILES, instance=user.profile, user_instance=user)
        password_form = PasswordChangeForm(user, request.POST)
        
        if 'profilePicture' in request.FILES or any(field in request.POST for field in form.fields):
            if form.is_valid():
                if not form.has_changed():
                    messages.success(request,'Profile is unchanged',extra_tags='profileInfoSuccess')
                else:
                    newEmail = form.cleaned_data['email']
                    newEnableEmailNotifications = form.cleaned_data['enableEmailNotifications']
                    if newEmail != user.email:
                        user.email_verified = False
                        notifications = Notifications (
                            name = f'Email Changed from {user.email} to {newEmail}',
                            date = timezone.now(),
                            user = user,
                        )
                    if user.email_verified:
                        profile.enableEmailNotifications = bool(newEnableEmailNotifications)
                    form.save()
                    user.save()
                    notifications = Notifications (
                        name = 'Profile Info Updated',
                        date = timezone.now(),
                        user = user,
                    )
                    notifications.notificationsCount += 1
                    notifications.save()
                    messages.success(request, 'Profile updated successfully',extra_tags='profileInfoSuccess')
            else:
                messages.error(request, 'Profile update failed',extra_tags='profileInfoError')
                
        if any(field in request.POST for field in password_form.fields):
            if password_form.is_valid():
                password_form.save()
                notifications = Notifications (
                    name = 'Profile password changed',
                    date = timezone.now(),
                    user = user,
                )
                notifications.notificationsCount += 1
                notifications.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Password changed successfully',extra_tags='profilePassSuccess')
            elif password_form.is_empty():
                password_form.clear_errors()
            else:
                messages.error(request, 'Password update failed.',extra_tags='profilePassError')

        return render(request, 'profile.html', {'form': form, 'password_form': password_form})
    else:
        form = ProfileForm(instance=user.profile, user_instance=user)
        password_form = PasswordChangeForm(user)

    return render(request, 'profile.html', {
        'form': form,
        'password_form': password_form
    })
    
######################## For Showing Notifications in reverse order
def notifications(request):
    notifications = Notifications.objects.filter(user=request.user)
    notifications.update(unread=False)
    request.user.notificationsCount = 0
    request.user.save()
    context = {
        'notifications': notifications.order_by('-id'),
    }
    return render(request, 'notifications.html', context)

#######################this function is used for ADDING task for that user
@login_required
def create_task(request):
    categories = Category.objects.filter(user=request.user)
    othersCategory = Category.objects.filter(name='Others', user=request.user).first()
    cur_date_ = timezone.now()
    cur_date = timezone.now() + timedelta(minutes=6)
    context = {
        'categories': categories,
        'cur_date_': cur_date_,
        'cur_date': cur_date,
        'othersCategory':othersCategory
    }
    if request.method == "POST":
        title = request.POST['title']
        description = request.POST['description']
        category_id = request.POST['category']
        try:
            category = Category.objects.get(id=category_id)
        except:
            messages.error(request, 'Category not found',extra_tags='createTaskError')
            return render(request, 'createTask.html', context)
        dueDate = request.POST['dueDate']
        important = request.POST.get('important')
        due_datetime = datetime.strptime(f"{dueDate}", '%Y-%m-%dT%H:%M')
        min_due_datetime = timezone.now() + timedelta(minutes=5)
        due_datetime = timezone.make_aware(due_datetime, timezone.get_current_timezone())
        notificationTime = 4
        emailNotification = False
        if request.user.profile.enableEmailNotifications:
            notificationTime = request.POST['notificationTime']
            emailNotification = request.POST.get('emailNotification')
        else:
            notificationTime = 4
            emailNotification = False
        if due_datetime <= min_due_datetime:
            notifications = Notifications (
                name = f'Due datetime must be at least 5 minutes from now. You entered {due_datetime.strftime("%Y-%m-%d | %H:%M")}',
                date = timezone.now(),
                user = request.user,
            )
            notifications.notificationsCount += 1
            notifications.save()
            due_datetime = timezone.now() + timedelta(minutes=5)
        
        task = Task(
            taskTitle=title,
            description=description,
            category=category,
            dueDate=due_datetime,
            user=request.user,
            important=important,
            emailNotification=bool(emailNotification),
            notificationTime=notificationTime,
        )
        try:
            task.save()
            notifications = Notifications (
                name = f'Task "{title}" Added',
                date = timezone.now(),
                user = request.user,
            )
            notifications.notificationsCount += 1
            notifications.save()
            messages.success(request,'Task created successfully',extra_tags='createTaskSuccess')
        except:
            messages.error(request, 'Task creation failed',extra_tags='createTaskError')
            return render(request, 'createTask.html', context)
    if not categories:
        context['no_categories'] = True
    
    return render(request, 'createTask.html', context)


#######################this function shows all the running tasks of that user
def running_tasks(request):
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'important')
    order = request.GET.get('order', 'desc')
    
    tasks_queryset = Task.objects.filter(user=request.user).filter(Q(status=Task.PENDING) | Q(status=Task.OVERDUE))

    if sort_by and order:
        if order == 'asc':
            tasks_queryset = tasks_queryset.order_by(sort_by)
        elif order == 'desc':
            tasks_queryset = tasks_queryset.order_by(F(sort_by).desc())
    else:
        tasks_queryset = tasks_queryset.order_by('-important', '-status', '-dueDate')
        
    paginator = Paginator(tasks_queryset, 10)
    page = request.GET.get('page')

    try:
        tasks = paginator.page(page)
    except PageNotAnInteger:
        tasks = paginator.page(1)
    except EmptyPage:
        tasks = paginator.page(paginator.num_pages)

    is_refreshed = request.GET.get('refresh', False)
    task_count = tasks_queryset.count()
    if not is_refreshed:
        if search_query:
            tasks = tasks_queryset.filter(taskTitle__icontains=search_query)
            task_count = tasks.count()

        if not task_count and search_query:
            messages.error(request, f'Task "{search_query}" wasn\'t found.',extra_tags='runningTaskError')
        elif task_count and search_query:
            messages.success(request, f'[{task_count}] tasks found matching your search query.',extra_tags='runningTaskSuccess')
        elif not task_count and not search_query:
            messages.error(request, 'You haven\'t created any tasks yet.',extra_tags='runningTaskError')

    context = {
        'tasks': tasks,
        'search_query': search_query,
    }
    return render(request, 'runningTasks.html', context)

#######################this function edits the specific running task of that user
@login_required  
def edit_task(request, task_id):
    try:
        task = get_object_or_404(Task, encrypted_id=task_id, user=request.user)
    except:
        messages.error(request, 'Task not found',extra_tags='runningTaskError')
        return redirect('running_tasks')
    categories = Category.objects.filter(user=request.user)
    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        category = get_object_or_404(Category, id=category_id)
        important = request.POST.get('important')
        notificationTime = task.notificationTime
        emailNotification = task.emailNotification
        if request.user.profile.enableEmailNotifications:
            notificationTime = request.POST.get('notificationTime')
            emailNotification = request.POST.get('emailNotification')

        if category is None:
            return HttpResponse("Category not found", status=404)

        dueDate = request.POST.get('dueDate')

        due_datetime = datetime.strptime(f"{dueDate}", '%Y-%m-%dT%H:%M')
        min_due_datetime = timezone.now() + timedelta(minutes=5)
        due_datetime = timezone.make_aware(due_datetime, timezone.get_current_timezone())

        if due_datetime <= min_due_datetime:
            due_datetime = timezone.now() + timedelta(minutes=5)

        task.taskTitle = title
        task.description = description
        task.category = category
        task.dueDate = due_datetime
        task.emailNotification = bool(emailNotification)
        task.notificationTime = notificationTime
        task.important = important
        task.status = Task.PENDING
        task.sent_reminder = False
        try:
            task.save()
            notifications = Notifications (
                name = f'Task "{title}" Updated',
                date = timezone.now(),
                user = request.user,
            )
            notifications.notificationsCount += 1
            notifications.save()
            messages.success(request, 'Task edited successfully',extra_tags='runningTaskSuccess')
        except:
            messages.error(request, 'Task edit failed',extra_tags='runningTaskError')
        return redirect('running_tasks') 
    
    context = {'task': task, 'categories': categories}
    return render(request, 'editTask.html', context)

#######################this function is used for completing tasks 
@require_POST
def mark_task_completed(request, task_id):
    task = get_object_or_404(Task, encrypted_id=task_id, user=request.user)
    if task is None:
        messages.error(request, 'Task not found', extra_tags='runningTaskError')
        return redirect('running_tasks')
    task.completedDate = timezone.now()
    task.status = Task.COMPLETED
    task.save()

    notifications = Notifications (
        name = f'Task "{task.taskTitle}" Marked as Completed',
        date = timezone.now(),
        user = request.user,
    )
    notifications.notificationsCount += 1
    notifications.save()
    profile = Profile.objects.get(user=request.user)
    profile.completedTasksCount += 1
    profile.save()
    
    messages.success(request,'Task marked as completed',extra_tags='runningTaskSuccess')
    return redirect('running_tasks')

#######################this function deletes that specific task details from running tasks of that user
@login_required 
def delete_task(request, task_id):
    try:
        task = get_object_or_404(Task, encrypted_id=task_id, user=request.user)
    except:
        messages.error(request,'Task not found',extra_tags='runningTaskError')
        return redirect('running_task')
    notifications = Notifications (
        name = f'Task "{task.taskTitle}" Deleted',
        date = timezone.now(),
        user = request.user,
    )
    notifications.notificationsCount += 1
    notifications.save()
    task.delete()
    
    messages.success(request, 'Task deleted successfully.',extra_tags='runningTaskSuccess')
    return redirect('running_tasks')

#######################this function shows the completed tasks of that user
@login_required
def completed_tasks(request):
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'completedDate')
    order = request.GET.get('order', 'desc')

    task_queryset = Task.objects.filter(user=request.user).filter(status=Task.COMPLETED)
    if sort_by and order:
        if order == 'asc':
            task_queryset = task_queryset.order_by(sort_by)
        elif order == 'desc':
            task_queryset = task_queryset.order_by(F(sort_by).desc())
    else:
        task_queryset = task_queryset.order_by( 'completedDate','-important', '-dueDate')
        
    paginator = Paginator(task_queryset, 10)
    page = request.GET.get('page')

    try:
        completed_tasks = paginator.page(page)
    except PageNotAnInteger:
        completed_tasks = paginator.page(1)
    except EmptyPage:
        completed_tasks = paginator.page(paginator.num_pages)
        
    is_refreshed = request.GET.get('refresh', False)
    task_count = task_queryset.count()
    if not is_refreshed:
        if search_query:
            completed_tasks = task_queryset.filter(taskTitle__icontains=search_query)
            task_count = completed_tasks.count()
        if not task_count and search_query:
            messages.error(request, f'Task "{search_query}" wasn\'t found.',extra_tags='completedTaskError')
        elif task_count and search_query:
            messages.success(request, f'[{task_count}] tasks found matching your search query.',extra_tags='completedTaskSuccess')
        elif not task_count and not search_query:
            messages.error(request, 'You haven\'t completed any tasks yet.',extra_tags='completedTaskError')
    context = {
        'completed_tasks': completed_tasks,
        'search_query': search_query,
    }
    
    return render(request, 'completedTasks.html', context)

#######################this function clears all those completed task details of that user
@login_required
def clear_history(request):
    completedTaskCount = Task.objects.filter(Q(status = Task.COMPLETED),user=request.user).count()
    if completedTaskCount is None:
        messages.error(request, 'Completed task list is empty',extra_tags='completedTaskError')
        return redirect('completed_tasks')
    Task.objects.filter(Q(status = Task.COMPLETED),user=request.user).delete()
    notifications = Notifications (
        name = f'Completed Tasks({completedTaskCount}) History Cleared',
        date = timezone.now(),
        user = request.user,
    )
    notifications.notificationsCount += 1
    notifications.save()
    
    messages.success(request, 'Completed tasks history has been cleared.',extra_tags='completedTaskSuccess')
    return redirect('completed_tasks')

#######################this function adds a category for that user
@login_required
def add_category(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST['name']
        existing_category = Category.objects.filter(name=name, user=request.user).first()
        if existing_category:
            messages.error(request, 'Category already exists.',extra_tags='categoryError')
            return redirect('add_category')
        else:
            category = Category(name=name, user=request.user)
            category.save()
            notifications = Notifications(
                name = f'Category "{name}" Added',
                date = timezone.now(),
                user = request.user,
            )
            notifications.notificationsCount += 1
            notifications.save()
            messages.success(request, 'Category added successfully!',extra_tags='categorySuccess')
    categories = Category.objects.filter(user=request.user)
    
    context = {
        'categories': categories,
    }
    return render(request, 'showCategories.html', context)

#######################this function is used to show the categories and all those tasks that the user has
@login_required
def all_categories(request, category_id=None):
    categories = Category.objects.filter(user=request.user)
    categories = categories.order_by('id')
    sort_by = request.GET.get('sort', 'important')
    order = request.GET.get('order', 'desc')
    tasks = Task.objects.all()
    
    if category_id is not None:
        tasks = tasks.filter(category_id=category_id)
        tasks = tasks.order_by('important','-status', '-dueDate')
        if sort_by and order:
            if order == 'asc':
                tasks = tasks.order_by(sort_by)
            elif order == 'desc':
                tasks = tasks.order_by(F(sort_by).desc())
            else:
                tasks = tasks.order_by('-important', '-completedDate', '-dueDate')
    
    context = {
        'categories': categories,
        'tasks': tasks,
    }
    if not categories:
        messages.error(request, 'No category found',extra_tags='categoryError')
    
    return render(request, 'showCategories.html', context)

#######################this function deletes specific category along with those associated tasks of that user
@login_required
def delete_category(request, category_id):
    try:
        category = get_object_or_404(Category, id=category_id, user=request.user)
    except:
        messages.error(request, 'Category not found',extra_tags='categoryError')
        return redirect('all_categories')
    categoryName = category.name
    if categoryName == 'Others':
        taskCount = Task.objects.filter(category=category).count()
        if taskCount == 0:
            messages.error(request, 'Category is empty!',extra_tags='categoryError')
            return redirect('all_categories')
        Task.objects.filter(category=category).delete()
        messages.success(request, 'Tasks in Others category deleted successfully',extra_tags='categorySuccess')
        notifications = Notifications (
            name = f'Tasks in "{categoryName}({taskCount})" Deleted',
            date = timezone.now(),
            user = request.user,
        )
        notifications.notificationsCount += 1
        notifications.save()
        return redirect('all_categories')
    taskCount = Task.objects.filter(category=category).count()
    try:
        category.delete()
        notifications = Notifications (
            name = f'Category "{categoryName}({taskCount})" Deleted',
            date = timezone.now(),
            user = request.user,
        )
        notifications.notificationsCount += 1
        notifications.save()
        messages.success(request,'Category deleted successfully',extra_tags='categorySuccess')
    except:
        messages.error(request,'Category deletion failed',extra_tags='categoryError')
    
    return redirect('all_categories')
#######################this function is used to delete user account
@login_required
def delete_account(request, user_id):
    user = get_object_or_404(CustomUser, encrypted_id=user_id)
    
    if user.is_superuser:
        notifications = Notifications(
            name='Admin Account Deletion Failed',
            date=timezone.now(),
            user=request.user,
        )
        notifications.notificationsCount += 1
        notifications.save()
        messages.error(request, f'Admin account can only be deleted from the admin page.',extra_tags='profileInfoError')
        return redirect('profile')
    
    if request.method == 'POST':
        confirm = request.POST.get('delAccConfirm', '')
        password = request.POST.get('delAccPassword', '')
        
        if confirm == 'CONFIRM' and user.check_password(password):
            user_media_path = os.path.join(settings.MEDIA_ROOT, 'profile_pictures', str(user.id))
            if os.path.exists(user_media_path):
                shutil.rmtree(user_media_path)
            user.delete()
            messages.success(request, 'Account deleted successfully.',extra_tags='authSuccess')
            logout(request)
            return redirect('signin')
        else:
            messages.error(request, 'Confirmation text or password is incorrect.',extra_tags='profileInfoError')
            return render(request, 'profile.html', {'textWrong': True, 'passWrong': True})
    
    return render(request, 'authentication.html', {'user': user})

########################this function is used to download the csv file of all the tasks of that user
@login_required
def export_tasks(request):
    tasks_queryset = Task.objects.filter(user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tasks.csv"'

    writer = csv.writer(response)
    writer.writerow(['Task Title', 'Description', 'Category', 'Created Date', 'Due Date', 'Completed Date', 'Priority', 'Status'])
    
    for task in tasks_queryset:
        writer.writerow([
            task.taskTitle,
            task.description,
            task.category.name,
            task.createdDate.strftime('%Y-%m-%d %H:%M:%S'),
            task.dueDate.strftime('%Y-%m-%d %H:%M:%S'),
            task.completedDate.strftime('%Y-%m-%d %H:%M:%S') if task.completedDate else '',
            task.get_important_display(),
            task.get_status_display()
        ])
    
    notifications = Notifications(
        name='Tasks Exported to CSV',
        date=timezone.now(),
        user=request.user,
    )
    notifications.notificationsCount += 1
    notifications.save()
    
    return response
####################this function is used to download the pdf file of all the tasks of that userclass ExportPDF(View):
class ExportPDF(View):
    def get(self, request):
        user = request.user
        
        tasks = Task.objects.filter(user=user)
        profile = Profile.objects.filter(user=user).first()
        template = get_template('generatePDF.html')

        profile_picture_base64 = None
        if profile and profile.profilePicture:
            profile_picture_path = default_storage.path(profile.profilePicture.name)
            with open(profile_picture_path, 'rb') as f:
                image = Image.open(f)
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                profile_picture_base64 = base64.b64encode(buffered.getvalue()).decode()

        context = {
            'user': user,
            'tasks': tasks,
            'profile': profile,
            'profile_picture_base64': profile_picture_base64,
        }

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="tasks.pdf"'

        html_content = template.render(context)

        pdf_file = BytesIO()
        HTML(string=html_content).write_pdf(pdf_file)

        response.write(pdf_file.getvalue())
        pdf_file.close()
        notifications = Notifications (
            name = 'Tasks Exported to PDF',
            date = timezone.now(),
            user = user,
        )
        notifications.notificationsCount += 1
        notifications.save()
        return response
