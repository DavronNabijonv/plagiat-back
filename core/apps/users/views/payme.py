from django.conf import settings

from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from payme.views import PaymeWebHookAPIView
from payme import Payme
from payme.models import PaymeTransactions

from core.apps.shared.models import Order
from core.apps.shared.tasks.generate_certificate import generate_certificate_pdf

payme = Payme(payme_id=settings.PAYME_ID)

class PaymeCallBackAPIView(PaymeWebHookAPIView):
    def handle_successfully_payment(self, params, result, *args, **kwargs):
        transaction_id = params.get("id")
        transaction = PaymeTransactions.objects.filter(transaction_id=transaction_id).first()
        order = Order.objects.filter(id=transaction.account_id, type="certificate").first()
        generate_certificate_pdf.delay(
            document_id=int(order.document.id),
            base_url=str(self.request.build_absolute_uri('/')),
        )

        print(f"Transaction successfully performed for this params: {params} and performed_result: {result}")

    def handle_cancelled_payment(self, params, result, *args, **kwargs):

        print(f"Transaction cancelled for this params: {params} and cancelled_result: {result}")


class PaymeLinkCreateApiView(GenericAPIView):
    serializer_class = None
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.filter(id=order_id).first()
            if not order:
                return Response({"error": "Order not found"})
            url = ""
            if order.type == "document":
                url = f"https://anti-plagiat.uz/uz/{order.document.id}"
            elif order.type == "ai_document":
                url = f"https://anti-plagiat.uz/uz/si/{order.ai_document.id}"
            else:
                url = f"https://anti-plagiat.uz/uz/{order.document.id}"
            payment_link = payme.initializer.generate_pay_link(
                id=order.id,
                amount=order.total_price,
                return_url=url,
            )
            return Response({"payment_link": payment_link})
        except Exception as e:
            return Response({"error": str(e)})
