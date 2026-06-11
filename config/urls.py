from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.apps.users.views.payme import PaymeCallBackAPIView
from core.apps.users.views.multicard import MulticardWebhookView

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
)


urlpatterns = [
    path('admin/', admin.site.urls),

    # drf-spectacular: OpenAPI sxema va Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    path('swagger/modern/', include('modern_drf_swagger.urls')),
    path('swagger/old/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    path('api/v1/', include(
        [
            path("users/", include("core.apps.users.urls")),
            path("shared/", include("core.apps.shared.urls")),
            path("bot/", include("core.apps.bot.urls")),
        ]
    )),
    path("payment/update/", PaymeCallBackAPIView.as_view()),
    path("payment/multicard/", MulticardWebhookView.as_view()),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
