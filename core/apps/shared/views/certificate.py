import re

from decimal import Decimal
from django.http import HttpResponse
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.apps.shared.models import Document, Order
from core.apps.shared.serializers.certificate import CertificateDownloadSerializer
from core.apps.shared.utils.generate_certificate import _regenerate_pdf_with_overrides
from payme import Payme


class CertificateStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id: int):
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"detail": "Topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        if document.certificate_file:
            return Response({"status": "ready"})
        return Response({"status": "processing"})


class CertificateDownloadView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CertificateDownloadSerializer

    def post(self, request, document_id: int):
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"detail": "Topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CertificateDownloadSerializer(
            data=request.data,
            context={'request': request, 'document': document},
        )
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            pdf_bytes = _regenerate_pdf_with_overrides(
                request=request,
                document=document,
                full_name=data['full_name'],
                file_name=data['file_name'],
                document_type=data['type'],
            )
        except Exception:
            return Response(
                {"detail": "PDF tayyorlashda xatolik yuz berdi"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        safe_title = re.sub(r'[^\w\-]', '_', document.title)[:40]
        filename   = f"sertifikat_{safe_title}.pdf"

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class PayForCertificateApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id: int):
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"detail": "Hujjat topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        order = Order.objects.create(
            user=request.user,
            document=document,
            total_price=Decimal("20600.00"),
            type="certificate",
        )
        payme = Payme(payme_id=settings.PAYME_ID)
        payment_link = payme.initializer.generate_pay_link(
            id=order.id,
            amount=order.total_price,
            return_url=f"https://anti-plagiat.uz/uz/{order.document.id}"
        )

        return Response({
            "order_id": order.id,
            "payment_link": payment_link
        })
