from django.urls import path
from core.apps.users.views.register import RegisterAPIView

from rest_framework_simplejwt.views import TokenObtainPairView
from core.apps.users.views.payme import PaymeLinkCreateApiView


urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path("payme/link/<int:order_id>/", PaymeLinkCreateApiView.as_view(), name="payme-link"),
]
