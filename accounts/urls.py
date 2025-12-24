from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),  # ИЗМЕНИТЬ: register_view вместо register
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin/update-user/<int:user_id>/', views.update_user, name='update_user'),

    path('api/registration-keys/generate/', views.generate_registration_key, name='generate_registration_key'),
    path('api/registration-keys/active/', views.get_active_keys, name='get_active_keys'),
    path('api/registration-keys/<int:key_id>/revoke/', views.revoke_key, name='revoke_key'),
    path('api/check-registration-key/', views.check_registration_key, name='check_registration_key'),
]