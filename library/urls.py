from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('resources/', views.resource_list, name='resource_list'),
    path('resources/add/', views.add_resource, name='add_resource'),
    path('resources/<int:pk>/', views.resource_detail, name='resource_detail'),
    path('resources/<int:pk>/edit/', views.edit_resource, name='edit_resource'),
    path('resources/<int:pk>/delete/', views.delete_resource, name='delete_resource'),
    path('resources/<int:pk>/delete-ajax/', views.delete_resource_ajax, name='delete_resource_ajax'),
    path('resources/<int:pk>/bookmark/', views.bookmark_toggle, name='bookmark_toggle'),
    path('topics/<int:pk>/', views.topic_detail, name='topic_detail'),
    path('topics/manage/', views.manage_topics, name='manage_topics'),
    path('topics/manage/', RedirectView.as_view(pattern_name='topic_list', permanent=True)),
    path('review/<int:pk>/edit/', views.edit_review, name='edit_review'),
    path('review/<int:pk>/delete/', views.delete_review, name='delete_review'),
    path('topics/', views.topic_list, name='topic_list'),
    path('topics/add/', views.add_topic, name='add_topic'),
    path('topics/<int:pk>/edit/', views.edit_topic, name='edit_topic'),
    path('topics/<int:pk>/delete/', views.delete_topic, name='delete_topic'),
]