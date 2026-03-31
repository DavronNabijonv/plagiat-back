from django.urls import path

from core.apps.shared.views.document import DocumentCreateView, DocumentListApiView
from core.apps.shared.views.order import OrderListApiView

urlpatterns = [
    path('documents/', DocumentCreateView.as_view(), name='document-create'),
    path('documents/list/', DocumentListApiView.as_view(), name='document-list'),
    path('orders/', OrderListApiView.as_view(), name='order-list'),
]
