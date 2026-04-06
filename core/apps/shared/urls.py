from django.urls import path

from core.apps.shared.views.document import DocumentCreateView, DocumentListApiView, DocumentDetailApiView
from core.apps.shared.views.order import OrderListApiView
from core.apps.shared.views.certificate import CertificateDownloadView, CertificateStatusView
from core.apps.shared.views.document_type import DocumentTypeListAPIView


urlpatterns = [
    path('documents/', DocumentCreateView.as_view(), name='document-create'),
    path('documents/list/', DocumentListApiView.as_view(), name='document-list'),
    path('orders/', OrderListApiView.as_view(), name='order-list'),
    path(
        'certificate/<int:document_id>/status/',
            CertificateStatusView.as_view(),
            name='certificate_status',
        ),
    path(
        'certificate/<int:document_id>/download/',
        CertificateDownloadView.as_view(),
        name='certificate_download',
    ),
    path('documents/<int:id>/', DocumentDetailApiView.as_view()),
    path("document_types/", DocumentTypeListAPIView.as_view(), name='document_type-list'),
]
