from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', views.landing, name='landing'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Routes & tickets
    path('routes/', views.routes_view, name='routes'),
    path('routes/<int:route_id>/buy/', views.buy_ticket, name='buy_ticket'),
    path('tickets/', views.my_tickets, name='my_tickets'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:ticket_id>/cancel/', views.cancel_ticket, name='cancel_ticket'),

    # History, notifications, profile
    path('history/', views.history_view, name='history'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('profile/', views.profile_view, name='profile'),
    path('topup/', views.topup_view, name='topup'),
    path('scan/', views.scan_view, name='scan'),

    # Payments (PayMongo)
    path('payments/', include('payments.urls')),

    # Admin panel
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin-panel/users/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('admin-panel/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('admin-panel/routes/', views.admin_routes, name='admin_routes'),
    path('admin-panel/routes/add/', views.admin_route_add, name='admin_route_add'),
    path('admin-panel/routes/<int:route_id>/edit/', views.admin_route_edit, name='admin_route_edit'),
    path('admin-panel/routes/<int:route_id>/delete/', views.admin_delete_route, name='admin_delete_route'),
    path('admin-panel/tickets/', views.admin_tickets, name='admin_tickets'),
    path('admin-panel/tickets/<int:ticket_id>/edit/', views.admin_ticket_edit, name='admin_ticket_edit'),
    path('admin-panel/transactions/', views.admin_transactions, name='admin_transactions'),

    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='core/password_reset.html',
        email_template_name='core/password_reset_email.html',
        subject_template_name='core/password_reset_subject.txt',
        success_url='/password-reset/done/'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='core/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='core/password_reset_confirm.html',
        success_url='/password-reset-complete/'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='core/password_reset_complete.html'
    ), name='password_reset_complete'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)