from django.urls import path

from core.apps.shared.views.document import DocumentCreateView, DocumentListApiView, DocumentDetailApiView
from core.apps.shared.views.order import OrderListApiView
from core.apps.shared.views.certificate import certificate_pdf_view, certificate_view


urlpatterns = [
    path('documents/', DocumentCreateView.as_view(), name='document-create'),
    path('documents/list/', DocumentListApiView.as_view(), name='document-list'),
    path('orders/', OrderListApiView.as_view(), name='order-list'),
    path('certificate/<int:document_id>/', certificate_view, name='certificate'),
    path('certificate/<int:document_id>/pdf/', certificate_pdf_view, name='certificate_pdf'),

    path('documents/<int:id>/', DocumentDetailApiView.as_view()),
]
