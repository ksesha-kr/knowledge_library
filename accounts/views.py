import secrets
import string
from datetime import timedelta
import json

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, get_user_model, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .forms import CustomRegistrationForm, CustomAuthenticationForm
from .models import RegistrationKey
from library.models import Resource, Bookmark, Rating

User = get_user_model()


def is_superuser(user):
    return user.is_superuser


def register_view(request):
    if request.method == 'POST':
        form = CustomRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}! Регистрация успешна.')

                if user.is_superuser:
                    return redirect('admin_dashboard')
                elif user.is_staff:
                    return redirect('profile')
                else:
                    return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = CustomRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')

                if user.is_superuser:
                    return redirect('admin_dashboard')
                else:
                    return redirect('profile')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('home')


@login_required
def profile_view(request):
    user_resources = Resource.objects.filter(author=request.user)
    user_bookmarks = Bookmark.objects.filter(user=request.user)
    user_ratings = Rating.objects.filter(user=request.user)

    context = {
        'user_resources': user_resources,
        'user_bookmarks': user_bookmarks,
        'user_ratings': user_ratings,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()
        messages.success(request, 'Профиль обновлен!')
        return redirect('profile')

    return render(request, 'accounts/edit_profile.html')


def is_admin(user):
    return user.is_superuser or user.is_staff


@login_required
@user_passes_test(is_superuser)
def admin_dashboard(request):
    total_users = User.objects.count()
    admins = User.objects.filter(is_superuser=True).count()
    teachers = User.objects.filter(is_staff=True, is_superuser=False).count()
    students = total_users - admins - teachers

    context = {
        'stats': {
            'total_users': total_users,
            'admins': admins,
            'teachers': teachers,
            'students': students,
        },
        'users': User.objects.all().order_by('-date_joined')
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
@user_passes_test(is_superuser)
def delete_user(request, user_id):
    if request.method == 'DELETE':
        try:
            user = User.objects.get(id=user_id)
            if user == request.user:
                return JsonResponse({
                    'success': False,
                    'error': 'Вы не можете удалить свой аккаунт'
                })

            if user.is_superuser:
                return JsonResponse({
                    'success': False,
                    'error': 'Нельзя удалить администратора'
                })

            username = user.username
            user.delete()

            return JsonResponse({
                'success': True,
                'message': f'Пользователь {username} удален'
            })

        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Пользователь не найден'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({'success': False, 'error': 'Метод не разрешен'})


@login_required
@user_passes_test(is_superuser)
def update_user(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)

            is_staff = request.POST.get('is_staff') == 'true'
            is_superuser = request.POST.get('is_superuser') == 'true'
            is_active = request.POST.get('is_active') == 'on'

            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.is_active = is_active
            user.save()

            return JsonResponse({
                'success': True,
                'message': 'Пользователь обновлен'
            })

        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Пользователь не найден'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({'success': False, 'error': 'Метод не разрешен'})


@login_required
@user_passes_test(is_admin)
@csrf_exempt
def generate_registration_key(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не разрешен'}, status=405)

    try:
        data = json.loads(request.body)

        role_mapping = {
            'viewer': 'student',
            'editor': 'teacher',
            'admin': 'admin',
        }

        frontend_role = data.get('role', 'viewer')
        backend_role = role_mapping.get(frontend_role, frontend_role)

        expiry_days = int(data.get('expiry_days', 7))
        max_uses = int(data.get('max_uses', 1))
        note = data.get('note', '')

        key = RegistrationKey.objects.create(
            created_by=request.user,
            role=backend_role,
            max_uses=max_uses,
            note=note
        )

        if expiry_days > 0:
            key.expires_at = timezone.now() + timedelta(days=expiry_days)
            key.save()

        return JsonResponse({
            'success': True,
            'key': {
                'id': key.id,
                'key': key.key,
                'role': key.role,
                'expires_at': key.expires_at.isoformat() if key.expires_at else None,
                'max_uses': key.max_uses,
                'uses': key.uses,
                'note': key.note,
                'created_at': key.created_at.isoformat(),
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@user_passes_test(is_admin)
def get_active_keys(request):
    try:
        keys = RegistrationKey.objects.filter(
            created_by=request.user,
            is_active=True
        ).order_by('-created_at')

        keys_list = []
        for key in keys:
            keys_list.append({
                'id': key.id,
                'key': key.key,
                'role': key.role,
                'expires_at': key.expires_at.isoformat() if key.expires_at else None,
                'max_uses': key.max_uses,
                'uses': key.uses,
                'note': key.note,
                'created_at': key.created_at.isoformat(),
            })

        return JsonResponse({
            'success': True,
            'keys': keys_list
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@user_passes_test(is_admin)
@csrf_exempt
def revoke_key(request, key_id):
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Метод не разрешен'}, status=405)

    try:
        key = RegistrationKey.objects.get(id=key_id, created_by=request.user)
        key.is_active = False
        key.save()

        return JsonResponse({'success': True})

    except RegistrationKey.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ключ не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
def check_registration_key(request):
    if request.method == 'GET':
        key_value = request.GET.get('key', '').strip()

        if not key_value:
            return JsonResponse({'valid': False, 'message': 'Введите ключ'})

        try:
            key = RegistrationKey.objects.get(key=key_value)

            if not key.is_active:
                return JsonResponse({
                    'valid': False,
                    'message': 'Ключ неактивен'
                })

            if key.expires_at and timezone.now() > key.expires_at:
                return JsonResponse({
                    'valid': False,
                    'message': 'Срок действия ключа истек'
                })

            if key.max_uses > 0 and key.uses >= key.max_uses:
                return JsonResponse({
                    'valid': False,
                    'message': 'Ключ использован максимальное число раз'
                })

            return JsonResponse({
                'valid': True,
                'message': 'Ключ действителен',
                'role': key.role,
                'role_name': key.get_role_display(),
                'expires_at': key.expires_at.isoformat() if key.expires_at else None,
                'uses_left': key.max_uses - key.uses if key.max_uses > 0 else '∞'
            })

        except RegistrationKey.DoesNotExist:
            return JsonResponse({'valid': False, 'message': 'Ключ не найден'})

    return JsonResponse({'valid': False, 'message': 'Неверный метод запроса'})