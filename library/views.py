import json

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model, login

from .models import Resource, Topic, Rating, Bookmark
from .forms import ResourceForm, SearchForm, RatingForm, TopicForm

User = settings.AUTH_USER_MODEL

def home(request):
    latest_resources = Resource.objects.all()[:10]
    popular_resources = Resource.objects.annotate(
        avg_rating=Avg('ratings__rating'),
        rating_count=Count('ratings')
    ).order_by('-avg_rating', '-rating_count')[:10]

    topics = Topic.objects.all()[:8]

    context = {
        'latest_resources': latest_resources,
        'popular_resources': popular_resources,
        'topics': topics,
    }
    return render(request, 'library/home.html', context)

def resource_list(request):
    form = SearchForm(request.GET or None)
    resources = Resource.objects.all()

    if form.is_valid():
        query = form.cleaned_data.get('query')
        resource_type = form.cleaned_data.get('resource_type')
        topic = form.cleaned_data.get('topic')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')

        if query:
            resources = resources.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )

        if resource_type:
            resources = resources.filter(resource_type=resource_type)

        if topic:
            resources = resources.filter(topics=topic)

        if date_from:
            resources = resources.filter(created_at__date__gte=date_from)

        if date_to:
            resources = resources.filter(created_at__date__lte=date_to)

    paginator = Paginator(resources, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'form': form,
        'search_query': request.GET.get('query', ''),
    }
    return render(request, 'library/resource_list.html', context)


def resource_detail(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    user_rating = None
    is_bookmarked = False

    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(
            resource=resource,
            user=request.user
        ).first()
        is_bookmarked = Bookmark.objects.filter(
            resource=resource,
            user=request.user
        ).exists()

    can_edit = False
    can_delete = False

    if request.user.is_authenticated:
        can_edit = (request.user.role in ['teacher', 'admin'] or request.user == resource.author)
        can_delete = (request.user.role == 'admin' or request.user == resource.author)

    if request.method == 'POST' and request.user.is_authenticated:
        rating_form = RatingForm(request.POST)
        if rating_form.is_valid():
            rating, created = Rating.objects.update_or_create(
                resource=resource,
                user=request.user,
                defaults=rating_form.cleaned_data
            )
            messages.success(request, 'Оценка сохранена!')
            return redirect('resource_detail', pk=pk)
    else:
        rating_form = RatingForm()

    context = {
        'resource': resource,
        'user_rating': user_rating,
        'is_bookmarked': is_bookmarked,
        'rating_form': rating_form,
        'can_edit': can_edit,
        'can_delete': can_delete,
    }
    return render(request, 'library/resource_detail.html', context)

@login_required
def add_resource(request):
    if request.user.role not in ['teacher', 'admin']:
        messages.error(request, 'Только преподаватели могут добавлять материалы')
        return redirect('home')

    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.author = request.user
            resource.save()
            form.save_m2m()  # Сохраняем связи многие-ко-многим
            messages.success(request, 'Материал успешно добавлен!')
            return redirect('resource_detail', pk=resource.pk)
    else:
        form = ResourceForm()

    all_users = []
    if request.user.role == 'admin':
        from accounts.models import CustomUser
        all_users = CustomUser.objects.all()

    context = {
        'form': form,
        'title': 'Добавление нового материала',
        'all_users': all_users,
    }
    return render(request, 'library/resource_form.html', context)

@login_required
def bookmark_toggle(request, pk):
    resource = get_object_or_404(Resource, pk=pk)

    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        resource=resource
    )

    if not created:
        bookmark.delete()
        messages.success(request, 'Удалено из избранного')
    else:
        messages.success(request, 'Добавлено в избранное')

    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def profile(request):
    user_resources = Resource.objects.filter(author=request.user)
    user_bookmarks = Bookmark.objects.filter(user=request.user)
    user_ratings = Rating.objects.filter(user=request.user)

    context = {
        'user_resources': user_resources,
        'user_bookmarks': user_bookmarks,
        'user_ratings': user_ratings,
    }
    return render(request, 'accounts/profile.html', context)

def topic_detail(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    resources = Resource.objects.filter(topics=topic)

    context = {
        'topic': topic,
        'resources': resources,
    }
    return render(request, 'library/topic_detail.html', context)

def is_teacher_or_admin(user):
    return user.role in ['teacher', 'admin']

@user_passes_test(is_teacher_or_admin)
def manage_topics(request):
    return redirect('topic_list')


def topic_detail(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    resources = Resource.objects.filter(topics=topic)

    all_topics = Topic.objects.exclude(pk=pk).annotate(
        resource_count=Count('resource')
    ).order_by('-resource_count')[:6]

    video_count = resources.filter(resource_type='video').count()
    pdf_count = resources.filter(resource_type='pdf').count()
    link_count = resources.filter(resource_type='link').count()
    note_count = resources.filter(resource_type='note').count()

    unique_authors = resources.values('author').distinct().count()

    context = {
        'topic': topic,
        'resources': resources,
        'all_topics': all_topics,
        'video_count': video_count,
        'pdf_count': pdf_count,
        'link_count': link_count,
        'note_count': note_count,
        'unique_authors': unique_authors,
    }
    return render(request, 'library/topic_detail.html', context)

@login_required
def edit_resource(request, pk):
    resource = get_object_or_404(Resource, pk=pk)

    if not resource.can_edit(request.user):
        messages.error(request, 'У вас нет прав для редактирования этого материала')
        return redirect('resource_detail', pk=pk)

    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            if 'clear_file' in request.POST and request.POST['clear_file'] == 'on':
                if resource.file:
                    resource.file.delete(save=False)

            if request.user.role != 'admin' and 'author' in form.changed_data:
                messages.error(request, 'Вы не можете изменять автора материала')
                return redirect('edit_resource', pk=pk)

            if request.user.role != 'admin':
                form.instance.author = request.user

            form.save()
            messages.success(request, 'Материал успешно обновлен!')
            return redirect('resource_detail', pk=resource.pk)
    else:
        form = ResourceForm(instance=resource)

    all_users = []
    if request.user.role == 'admin':
        from accounts.models import CustomUser
        all_users = CustomUser.objects.all()

    context = {
        'form': form,
        'resource': resource,
        'title': 'Редактирование материала',
        'all_users': all_users,
    }
    return render(request, 'library/resource_form.html', context)

@login_required
def delete_resource(request, pk):
    resource = get_object_or_404(Resource, pk=pk)

    if not resource.can_delete(request.user):
        messages.error(request, 'У вас нет прав для удаления этого материала')
        return redirect('resource_detail', pk=pk)

    if request.method == 'POST':
        resource_title = resource.title
        resource.delete()
        messages.success(request, f'Материал "{resource_title}" успешно удален')
        return redirect('profile')

    context = {
        'resource': resource,
    }
    return render(request, 'library/resource_confirm_delete.html', context)


@login_required
def delete_resource_ajax(request, pk):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        resource = get_object_or_404(Resource, pk=pk)

        if not resource.can_delete(request.user):
            return JsonResponse({'success': False, 'error': 'Нет прав на удаление'})

        resource.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Неверный запрос'})


@login_required
def edit_review(request, pk):
    rating = get_object_or_404(Rating, pk=pk)

    if rating.user != request.user:
        messages.error(request, 'Вы не можете редактировать чужой отзыв')
        return redirect('resource_detail', pk=rating.resource.pk)

    if request.method == 'POST':
        rating.comment = request.POST.get('comment', '')
        rating.rating = int(request.POST.get('rating', 5))
        rating.save()

        messages.success(request, 'Отзыв успешно обновлен')
        return redirect('resource_detail', pk=rating.resource.pk)

    context = {
        'review': rating,
        'resource': rating.resource,
    }
    return render(request, 'library/edit_review.html', context)

@login_required
def delete_review(request, pk):
    rating = get_object_or_404(Rating, pk=pk)
    resource_pk = rating.resource.pk

    if rating.user != request.user and not request.user.is_staff:
        messages.error(request, 'Вы не можете удалить чужой отзыв')
        return redirect('resource_detail', pk=resource_pk)

    rating.delete()

    messages.success(request, 'Отзыв успешно удален')
    return redirect('resource_detail', pk=resource_pk)

def is_staff_user(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_user)
def topic_list(request):
    topics = Topic.objects.all().order_by('name')
    context = {
        'topics': topics,
        'title': 'Управление темами',
    }
    return render(request, 'library/topic_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def add_topic(request):
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save()
            messages.success(request, f'Тема "{topic.name}" успешно добавлена')
            return redirect('topic_list')
    else:
        form = TopicForm()

    context = {
        'form': form,
        'title': 'Добавить новую тему',
    }
    return render(request, 'library/topic_form.html', context)

def staff_required(view_func):
    decorated_view_func = login_required(user_passes_test(
        lambda u: u.is_staff or u.is_superuser,
        login_url='/'
    )(view_func))
    return decorated_view_func

@staff_required
def edit_topic(request, pk):
    topic = get_object_or_404(Topic, pk=pk)

    if request.method == 'POST':
        form = TopicForm(request.POST, instance=topic)
        if form.is_valid():
            form.save()
            messages.success(request, f'Тема "{topic.name}" успешно обновлена')
            return redirect('topic_list')
    else:
        form = TopicForm(instance=topic)

    context = {
        'form': form,
        'topic': topic,
        'title': f'Редактировать тему: {topic.name}',
    }
    return render(request, 'library/topic_form.html', context)

@staff_required
def delete_topic(request, pk):
    topic = get_object_or_404(Topic, pk=pk)

    if request.method == 'POST':
        topic_name = topic.name
        topic.delete()
        messages.success(request, f'Тема "{topic_name}" успешно удалена')
        return redirect('topic_list')

    context = {
        'topic': topic,
        'title': f'Удалить тему: {topic.name}',
    }
    return render(request, 'library/topic_confirm_delete.html', context)

def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
@require_http_methods(["GET"])
def get_active_registration_keys(request):
    try:
        keys = RegistrationKey.objects.filter(is_active=True).order_by('-created_at')

        keys_data = []
        for key in keys:
            keys_data.append({
                'id': key.id,
                'key': key.key,
                'role': key.role,
                'created_at': key.created_at.isoformat(),
                'expires_at': key.expires_at.isoformat() if key.expires_at else None,
                'max_uses': key.max_uses,
                'uses': key.uses,
                'note': key.note,
                'status': key.status
            })

        return JsonResponse({
            'success': True,
            'keys': keys_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@user_passes_test(is_superuser)
@csrf_exempt
@require_http_methods(["POST"])
def generate_registration_key(request):
    try:
        data = json.loads(request.body)

        role = data.get('role', RegistrationKey.ROLE_VIEWER)
        expiry_days = int(data.get('expiry_days', 7))
        max_uses = int(data.get('max_uses', 1))
        note = data.get('note', '')

        valid_roles = [choice[0] for choice in RegistrationKey.ROLE_CHOICES]
        if role not in valid_roles:
            return JsonResponse({
                'success': False,
                'error': 'Некорректная роль'
            }, status=400)

        registration_key = RegistrationKey.create_key(
            created_by=request.user,
            role=role,
            expiry_days=expiry_days,
            max_uses=max_uses,
            note=note
        )

        return JsonResponse({
            'success': True,
            'key': {
                'id': registration_key.id,
                'key': registration_key.key,
                'role': registration_key.role,
                'created_at': registration_key.created_at.isoformat(),
                'expires_at': registration_key.expires_at.isoformat() if registration_key.expires_at else None,
                'max_uses': registration_key.max_uses,
                'uses': registration_key.uses,
                'note': registration_key.note,
                'status': registration_key.status
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@user_passes_test(is_superuser)
@csrf_exempt
@require_http_methods(["DELETE"])
def revoke_registration_key(request, key_id):
    try:
        registration_key = RegistrationKey.objects.get(id=key_id, created_by=request.user)
        registration_key.revoke()

        return JsonResponse({
            'success': True,
            'message': 'Ключ успешно отозван'
        })
    except RegistrationKey.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Ключ не найден'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def register_with_key(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            registration_key = data.get('registration_key')
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            try:
                key = RegistrationKey.objects.get(key=registration_key)
            except RegistrationKey.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Неверный ключ регистрации'
                }, status=400)

            is_valid, message = key.is_valid()
            if not is_valid:
                return JsonResponse({
                    'success': False,
                    'error': message
                }, status=400)

            User = get_user_model()

            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Пользователь с таким именем уже существует'
                }, status=400)

            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Пользователь с таким email уже существует'
                }, status=400)

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            if key.role == RegistrationKey.ROLE_ADMIN:
                user.is_superuser = True
                user.is_staff = True
            elif key.role == RegistrationKey.ROLE_EDITOR:
                user.is_staff = True

            user.save()

            key.use_key()

            login(request, user)

            return JsonResponse({
                'success': True,
                'message': 'Регистрация успешна',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({
        'success': False,
        'error': 'Метод не разрешен'
    }, status=405)