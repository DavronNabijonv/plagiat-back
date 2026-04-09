from django.urls import path

from core.apps.bot.views.update_user import BotUserView
from core.apps.bot.views.check_user import CheckUserView

urlpatterns = [
    path('get_token/', BotUserView.as_view(), name='get_token'),
    path('check_user/<str:tg_id>/', CheckUserView.as_view(), name='check_user'),
]
