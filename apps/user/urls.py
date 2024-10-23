from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.SignupView.as_view(), name="register"),
    path('verify/<str:otp_secret>/', views.VerifyView.as_view(), name='verify'),
    path("login/", views.LoginView.as_view(), name="login"),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('avatars/', views.UserAvatarUploadView.as_view(), name='user-avatar'),
    path('avatars/<uuid:pk>/', views.UserAvatarRetrieveDestroy.as_view(), name='user-avatar-detail-delete'),
    path("logout/", views.LogoutView.as_view()),
    path('devices/', views.DeviceListView.as_view(), name='device-list'),
    path('contacts/', views.ContactListCreateView.as_view(), name='contact-list-create'),
    path('contacts/<uuid:pk>/', views.ContactDeleteView.as_view(), name='contact-delete'),
    path('contacts/sync/', views.ContactSyncView.as_view(), name='contact-sync'),
    path('2fa/verify/', views.Verify2FAView.as_view(), name='2fa-verify'),
    path('2fa/enable/', views.Enable2FAView.as_view(), name='2fa-enable'),
    path('status/<uuid:user_id>/', views.UserStatusView.as_view(), name='user-status'),
    path('notifications/', views.NotificationPreferenceView.as_view(), name='notification-preferences'),
]
