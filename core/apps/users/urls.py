from django.urls import path
from core.apps.users.views.register import RegisterAPIView


urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
]
