from django.urls import path
from . import views

urlpatterns = [
    path('', views.ChannelListCreateView.as_view(), name='channel-list'),
    path('<uuid:pk>/', views.ChannelRetrieveUpdateDestroyView.as_view(), name='channel-detail'),
    path('<uuid:pk>/memberships/', views.ChannelMembershipListCreateView.as_view(),
         name='membership-list-create'),
    path('<uuid:pk>/memberships/<uuid:membership_pk>/', views.ChannelMembershipUpdateDestroyView.as_view(),
         name='membership-detail'),
]
