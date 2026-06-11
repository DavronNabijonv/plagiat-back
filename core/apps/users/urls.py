from django.urls import path

from core.apps.users.views.register import RegisterAPIView
from core.apps.users.views.login import CustomTokenObtainPairView
from core.apps.users.views.user import UserProfileView
from core.apps.users.views.payme import (
    PaymeLinkCreateApiView,
    PaymentLinkView,
)
from core.apps.users.views.multicard import (
    MulticardCreateView,
    MulticardTopupCreateView,
)
from core.apps.users.views.balance import (
    PayWithBalanceView,
    BalanceView,
)


urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),

    # Yagona to'lov entry point: { "method": "multicard"|"balance" }
    path(
        'payment/link/<int:order_id>/',
        PaymentLinkView.as_view(),
        name='payment-link',
    ),

    # Multicard: xizmat to'lovi + balans to'ldirish
    path(
        'multicard/pay/<int:order_id>/',
        MulticardCreateView.as_view(),
        name='multicard-pay',
    ),
    path(
        'multicard/topup/',
        MulticardTopupCreateView.as_view(),
        name='multicard-topup',
    ),

    # Balans: joriy holat ko'rish + balansdan to'lash
    path('balance/', BalanceView.as_view(), name='balance'),
    path(
        'balance/pay/<int:order_id>/',
        PayWithBalanceView.as_view(),
        name='balance-pay',
    ),

    # Orqaga moslik
    path(
        'payme/link/<int:order_id>/',
        PaymeLinkCreateApiView.as_view(),
        name='payme-link',
    ),
]
