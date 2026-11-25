from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .browser_session import BrowserSessionView
from .views import RegisterView, CurrentUserView
from .views import (
    RegisterView,
    CurrentUserView,
    MyGuardianshipsView,
    GuardianRegistrationCreateView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('session/', BrowserSessionView.as_view(), name='browser-session'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path(
    'guardianships/',
    GuardianRegistrationCreateView.as_view(),
    name='guardian-create'
    ),
    path(
    'my-guardianships/',
    MyGuardianshipsView.as_view(),
    name='my-guardianships'
    ),
]
