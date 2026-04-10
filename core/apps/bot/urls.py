from django.urls import path, include

from core.apps.bot.views.update_or_create import UpdateUserView
from core.apps.bot.views.token import TokenView

urlpatterns = [
    path('user/', include(
        [
            path('update_or_create/', UpdateUserView.as_view(), name='update_or_create'),
            path('token/<str:tg_id>/', TokenView.as_view(), name='token'),
        ]
    )),
]
