from datetime import datetime

from django.db.models import IntegerField, Sum
from django.db.models.functions import Cast

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from drf_spectacular.utils import extend_schema, OpenApiResponse

from core.apps.shared.models import Document, AiDocument, Order
from payme.models import PaymeTransactions


class StatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Statistics'],
        summary="Foydalanuvchi statistikasi",
        description=(
            "Joriy foydalanuvchi bo'yicha umumiy ko'rsatkichlarni qaytaradi — "
            "dashboard sahifasi uchun.\n\n"
            "**Javob (200):**\n"
            "```json\n"
            "{\n"
            '  "total_documents": 12,\n'
            '  "this_month_documents": 3,\n'
            '  "paid_price": 145000\n'
            "}\n"
            "```\n"
            "- `total_documents` — jami hujjatlar (plagiat + AI)\n"
            "- `this_month_documents` — shu oyda yaratilganlari\n"
            "- `paid_price` — to'langan orderlar umumiy summasi (so'm)"
        ),
        responses={200: OpenApiResponse(description="Statistika ko'rsatkichlari")},
    )
    def get(self, request):
        user = request.user
        documents = Document.objects.filter(user=user)
        ai_documents = AiDocument.objects.filter(user=user)
        orders = Order.objects.filter(user=user)

        total_count = documents.count() + ai_documents.count()
        this_month_count = documents.filter(created_at__month=datetime.now().month).count() + ai_documents.filter(created_at__month=datetime.now().month).count()

        transactions = PaymeTransactions.objects.filter(
            state=PaymeTransactions.SUCCESSFULLY
        ).annotate(
            account_id_int=Cast("account_id", IntegerField())
        ).values_list("account_id_int", flat=True)

        paid_orders = orders.filter(id__in=transactions)

        paid_price = paid_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0

        return Response({
            'total_documents': total_count,
            'this_month_documents': this_month_count,
            'paid_price': paid_price,
        })
