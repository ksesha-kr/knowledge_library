from django.contrib import admin
from .models import Resource, Topic, Rating, Bookmark, ResourceTopic

class ResourceTopicInline(admin.TabularInline):
    model = ResourceTopic
    extra = 1

class RatingInline(admin.TabularInline):
    model = Rating
    extra = 0

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'resource_type', 'created_at']
    list_filter = ['resource_type', 'created_at', 'topics']
    search_fields = ['title', 'description']
    inlines = [ResourceTopicInline, RatingInline]
    filter_horizontal = ['topics']

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['resource', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource', 'created_at']
    list_filter = ['created_at']