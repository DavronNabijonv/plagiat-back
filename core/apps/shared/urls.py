from django.urls import path, include

from core.apps.shared.views.document import DocumentCreateView, DocumentListApiView, DocumentDetailApiView
from core.apps.shared.views.order import OrderListApiView
from core.apps.shared.views.certificate import CertificateDownloadView, CertificateStatusView
from core.apps.shared.views.document_type import DocumentTypeListAPIView
from core.apps.shared.views.ai_document import AiDocumentDetailApiView, AiDocumentListApiView, AiDocumentCreateView, PayForAiDocumentApiView


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
    
    path("ai_document/", include(
        [
            path('list/', AiDocumentListApiView.as_view(), name='ai_document-list'),
            path('create/', AiDocumentCreateView.as_view(), name='ai_document-create'),
            path('pay/<int:document_id>/', PayForAiDocumentApiView.as_view(), name='ai_document-pay'),
            path('<int:id>/', AiDocumentDetailApiView.as_view(), name='ai_document-detail'),
        ]
    ))
]
