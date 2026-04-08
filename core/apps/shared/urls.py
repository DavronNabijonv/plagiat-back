from django.urls import path, include

from core.apps.shared.views.document import DocumentCreateView, DocumentListApiView, DocumentDetailApiView
from core.apps.shared.views.order import OrderListApiView
from core.apps.shared.views.certificate import CertificateDownloadView, CertificateStatusView, PayForCertificateApiView
from core.apps.shared.views.document_type import DocumentTypeListAPIView
from core.apps.shared.views.ai_document import AiDocumentDetailApiView, AiDocumentListApiView, AiDocumentCreateView, PayForAiDocumentApiView
from core.apps.shared.views.statistics import StatisticsView
from core.apps.shared.views.payment_list import UnifiedOrderListView
from core.apps.shared.views.download_file import DocumentFileDownloadView, AiOrderFileDownloadView
from core.apps.shared.views.check_file import CheckFileView

urlpatterns = [
    # documents
    path('documents/', include(
        [
            path("", DocumentCreateView.as_view(), name='document-create'),
            path('list/', DocumentListApiView.as_view(), name='document-list'),
            path('<int:id>/', DocumentDetailApiView.as_view()),
            path('<int:id>/download/', DocumentFileDownloadView.as_view(), name='order-file-download'),
            path("types/", DocumentTypeListAPIView.as_view(), name='document_type-list'),
        ],
    )),

    # orders
    path('orders/', include(
        [
            path('', OrderListApiView.as_view(), name='order-list'),
            path('all/', UnifiedOrderListView.as_view(), name='unified-orders'),
        ]
    )),

    # certificate
    path('certificate/', include(
        [
            path('<int:document_id>/status/', CertificateStatusView.as_view(), name='certificate_status'),
            path('<int:document_id>/download/', CertificateDownloadView.as_view(), name='certificate_download'),
            # path('<int:document_id>/pay/', PayForCertificateApiView.as_view(), name='certificate_pay'),
        ]
    )),

    # ai document
    path("ai_document/", include(
        [
            path('list/', AiDocumentListApiView.as_view(), name='ai_document-list'),
            path('create/', AiDocumentCreateView.as_view(), name='ai_document-create'),
            # path('<int:id>/pay/', PayForAiDocumentApiView.as_view(), name='ai_document-pay'),
            path('<int:id>/', AiDocumentDetailApiView.as_view(), name='ai_document-detail'),
            path('<int:id>/download/', AiOrderFileDownloadView.as_view(), name='order-file-download'),
        ]
    )),

    # statistics
    path('statistics/', StatisticsView.as_view()),
    # file check
    path('check_file/', CheckFileView.as_view(), name='check-file'),
]
