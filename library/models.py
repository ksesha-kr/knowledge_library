import secrets
import string
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    color = models.CharField(max_length=7, default='#6c757d', verbose_name="Цвет")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Тема"
        verbose_name_plural = "Темы"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def material_count(self):
        return self.resources.count()

    @property
    def is_used(self):
        return self.resources.exists()


class Resource(models.Model):
    TYPE_CHOICES = [
        ('pdf', 'PDF документ'),
        ('video', 'Видео'),
        ('link', 'Ссылка'),
        ('note', 'Заметка'),
        ('presentation', 'Презентация'),
        ('book', 'Книга'),
    ]

    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    resource_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='Тип материала'
    )
    url = models.URLField(blank=True, verbose_name='URL')
    file = models.FileField(
        upload_to='resources/',
        blank=True,
        null=True,
        verbose_name='Файл'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resources',
        verbose_name='Автор'
    )
    topics = models.ManyToManyField(
        Topic,
        through='ResourceTopic',
        verbose_name='Темы'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return self.title

    def average_rating(self):
        ratings = self.ratings.all()
        if ratings:
            return sum(r.rating for r in ratings) / len(ratings)
        return 0

    def can_edit(self, user):
        if not user.is_authenticated:
            return False
        return user.role in ['teacher', 'admin'] or user == self.author

    def can_delete(self, user):
        if not user.is_authenticated:
            return False
        return user.role == 'admin' or user == self.author

    class Meta:
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'
        ordering = ['-created_at']

    @property
    def can_be_edited_by(self):
        pass

    def get_can_edit(self, user):
        return user.is_authenticated and (user.role in ['teacher', 'admin'] or user == self.author)

    def get_can_delete(self, user):
        return user.is_authenticated and (user.role == 'admin' or user == self.author)


class ResourceTopic(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['resource', 'topic']
        verbose_name = 'Связь материал-тема'
        verbose_name_plural = 'Связи материал-тема'


class Rating(models.Model):
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name='Материал'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name='Пользователь'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Оценка'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата оценки')

    class Meta:
        unique_together = ['resource', 'user']
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.resource}: {self.rating}"


class Bookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name='Пользователь'
    )
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name='Материал'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        unique_together = ['user', 'resource']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} -> {self.resource}"
