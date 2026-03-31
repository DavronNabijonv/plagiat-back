from django.urls import path
from core.apps.users.views.register import RegisterAPIView

from rest_framework_simplejwt.views import TokenObtainPairView


urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
]
