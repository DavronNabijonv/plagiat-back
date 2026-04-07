from django.urls import path

from core.apps.bot.views.update_user import BotUserView

urlpatterns = [
    path('get_token/', BotUserView.as_view(), name='get_token'),
]
