from django.urls import path, include

from core.apps.shared.views.document import DocumentCreateView, DocumentListApiView, DocumentDetailApiView
from core.apps.shared.views.order import OrderListApiView, AiOrderListApiView
from core.apps.shared.views.certificate import CertificateDownloadView, CertificateStatusView
from core.apps.shared.views.document_type import DocumentTypeListAPIView
from core.apps.shared.views.ai_document import AiDocumentDetailApiView, AiDocumentListApiView, AiDocumentCreateView, PayForAiDocumentApiView
from core.apps.shared.views.statistics import StatisticsView
from core.apps.shared.views.payment_list import UnifiedOrderListView
from core.apps.shared.views.download_file import OrderFileDownloadView, AiOrderFileDownloadView

urlpatterns = [
    path('documents/', DocumentCreateView.as_view(), name='document-create'),
    path('documents/list/', DocumentListApiView.as_view(), name='document-list'),
    path('orders/', OrderListApiView.as_view(), name='order-list'),
    path('ai_orders/', AiOrderListApiView.as_view(), name='order-list'),
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
    )),
    path('statistics/', StatisticsView.as_view()),
    path('orders/all/', UnifiedOrderListView.as_view(), name='unified-orders'),
    path('documents/<int:document_id>/download/', OrderFileDownloadView.as_view(), name='order-file-download'),
    path('ai_documents/<int:ai_document_id>/download/', AiOrderFileDownloadView.as_view(), name='order-file-download'),
]
