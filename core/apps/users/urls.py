from django.urls import path
from core.apps.users.views.register import RegisterAPIView

from core.apps.users.views.payme import PaymeLinkCreateApiView
from core.apps.users.views.login import CustomTokenObtainPairView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path("payme/link/<int:order_id>/", PaymeLinkCreateApiView.as_view(), name="payme-link"),
]
