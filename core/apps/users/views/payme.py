from django.conf import settings

from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from payme.views import PaymeWebHookAPIView
from payme import Payme
from core.apps.shared.models import Order

payme = Payme(payme_id=settings.PAYME_ID)

class PaymeCallBackAPIView(PaymeWebHookAPIView):


    def handle_successfully_payment(self, params, result, *args, **kwargs):
        """
        Handle the successful payment. You can override this method
        """
        print(f"Transaction successfully performed for this params: {params} and performed_result: {result}")

    def handle_cancelled_payment(self, params, result, *args, **kwargs):
        """
        Handle the cancelled payment. You can override this method
        """
        print(f"Transaction cancelled for this params: {params} and cancelled_result: {result}")


class PaymeLinkCreateApiView(GenericAPIView):
    serializer_class = None
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.filter(id=order_id).first()
            if not order:
                return Response({"error": "Order not found"})
            payment_link = payme.initializer.generate_pay_link(
                id=order_id,
                amount=order.total_price,
                return_url=f"https://anti-plagiat.uz/uz/{order.document.id}"
            )
            return Response({"payment_link": payment_link})
        except Exception as e:
            return Response({"error": str(e)})
