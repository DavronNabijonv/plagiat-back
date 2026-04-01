from django.urls import path

from core.apps.shared.views.document import DocumentCreateView, DocumentListApiView, DocumentDetailApiView
from core.apps.shared.views.order import OrderListApiView
from core.apps.shared.views.certificate import certificate_pdf_view

urlpatterns = [
    path('documents/', DocumentCreateView.as_view(), name='document-create'),
    path('documents/list/', DocumentListApiView.as_view(), name='document-list'),
    path('orders/', OrderListApiView.as_view(), name='order-list'),
    path('certificate/download/', certificate_pdf_view, name='certificate_download'),
    path('documents/<int:id>/', DocumentDetailApiView.as_view()),
]
