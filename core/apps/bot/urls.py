from django.urls import path

from core.apps.bot.views.register import RegisterView
from core.apps.bot.views.save_tg_id import SaveTelegramIdView
from core.apps.bot.views.login import LoginView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('save_tg_id/', SaveTelegramIdView.as_view(), name='save_tg_id'),
    path('login/', LoginView.as_view(), name='login'),
]
