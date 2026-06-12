import re

from decimal import Decimal
from django.http import HttpResponse
from django.conf import settings
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)

from core.apps.shared.models import Document, Order
from core.apps.shared.serializers.certificate import CertificateDownloadSerializer
from core.apps.shared.utils.generate_certificate import _regenerate_pdf_with_overrides
from payme import Payme


class CertificateStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Certificate'],
        summary="Sertifikat tayyorlik holatini tekshirish",
        description=(
            "Hujjat sertifikati (PDF) tayyor yoki hali generatsiya qilinayotganini "
            "qaytaradi. Sertifikat fonda (Celery) yaratiladi, shuning uchun "
            "tayyor bo'lguncha bu endpointni polling qilib turing.\n\n"
            "**Javob (200):**\n"
            "```json\n"
            '{ "status": "ready" }\n'
            "```\n"
            "yoki\n"
            "```json\n"
            '{ "status": "processing" }\n'
            "```\n"
            "`ready` bo'lgach `POST /shared/certificate/<document_id>/download/` "
            "orqali yuklab olish mumkin."
        ),
        parameters=[
            OpenApiParameter(
                name='document_id',
                type=int,
                location=OpenApiParameter.PATH,
                description="Hujjat ID si",
            ),
        ],
        responses={
            200: OpenApiResponse(description='"ready" yoki "processing" holati'),
            404: OpenApiResponse(description="Hujjat topilmadi"),
        },
    )
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

    @extend_schema(
        tags=['Certificate'],
        summary="Sertifikatni yuklab olish (PDF)",
        description=(
            "Sertifikat PDF faylini qaytaradi (`application/pdf`, attachment). "
            "Frontend javobni blob sifatida qabul qilib, faylni saqlashi kerak.\n\n"
            "**So'rov tanasi:**\n"
            "```json\n"
            "{\n"
            '  "full_name": "Ali Valiyev",\n'
            '  "file_name": "Dissertatsiya",\n'
            '  "document_type": 1\n'
            "}\n"
            "```\n"
            "- `full_name` — sertifikatda ko'rsatiladigan F.I.Sh (kamida 2 so'z)\n"
            "- `file_name` — sertifikatdagi ish nomi (`/ \\\\ : * ? \" < > |` "
            "belgilarisiz)\n"
            "- `document_type` — hujjat turi ID si\n\n"
            "**Xato holatlari:**\n"
            "- `402` — sertifikat uchun to'lov qilinmagan (20 600 so'm), javobda "
            "`code: \"not_paid\"` keladi\n"
            "- `400` — validatsiya xatosi yoki sertifikat hali tayyor emas "
            "(avval status endpointidan `ready` ni kuting)"
        ),
        parameters=[
            OpenApiParameter(
                name='document_id',
                type=int,
                location=OpenApiParameter.PATH,
                description="Hujjat ID si",
            ),
        ],
        responses={
            200: OpenApiResponse(description="PDF fayl (application/pdf, attachment)"),
            400: OpenApiResponse(description="Validatsiya xatosi yoki sertifikat tayyor emas"),
            402: OpenApiResponse(description="Sertifikat uchun to'lov qilinmagan"),
            404: OpenApiResponse(description="Hujjat topilmadi"),
            500: OpenApiResponse(description="PDF tayyorlashda server xatosi"),
        },
    )
    def post(self, request, document_id: int):
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"detail": "Topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CertificateDownloadSerializer(
            data=request.data,
            context={'request': request, 'document': document},
        )
        if not document.certificate:
            return Response(
                {
                    "success": False,
                    "error": "Sertifikat yuklab olish uchun to'lov qiling. 20600.00 so'm",
                    "code": "not_paid",
                    "amount": 20600.00
                }, status=status.HTTP_402_PAYMENT_REQUIRED
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

    @extend_schema(
        tags=['Certificate'],
        summary="Sertifikat uchun Payme havolasi (hozir ishlatilmaydi)",
        description=(
            "Sertifikat to'lovi uchun alohida order ochib, Payme havolasini "
            "qaytaradi. URL'da o'chirilgan — to'lov uchun "
            "`POST /users/payment/link/<order_id>/` dan foydalaning."
        ),
        deprecated=True,
    )
    @transaction.atomic
    def post(self, request, document_id: int):
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"detail": "Hujjat topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        order = Order.objects.create(
            user=request.user,
            document=document,
            type="certificate",
            total_price=Decimal("20600.00"),
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


class CertificateVerifyView(APIView):
    """
    BE-05: sertifikatdagi QR ochadigan ommaviy tasdiqlash endpointi.
    Login talab qilmaydi — frontend /verify/{id} sahifasi shu yerdan o'qiydi.
    """
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        tags=['Certificate'],
        summary="Sertifikatni ommaviy tasdiqlash (login talab qilinmaydi)",
        description=(
            "Sertifikatdagi QR-kod ochadigan sahifa uchun ma'lumot. Hujjat "
            "mavjud, to'langan va natijasi bor bo'lsa `valid: true` bilan "
            "asosiy ballarni qaytaradi.\n\n"
            "**Javob (200):**\n"
            "```json\n"
            "{\n"
            '  "valid": true,\n'
            '  "document_id": 10,\n'
            '  "certificate_number": "00000010 / A1B2C3D4",\n'
            '  "title": "Dissertatsiya mavzusi",\n'
            '  "owner_name": "Ali Valiyev",\n'
            '  "hash": "a1b2c3d4...",\n'
            '  "created_at": "2026-06-12T10:00:00Z",\n'
            '  "originality": 86, "plagiarism": 9, "citation": 5, "ai": 12\n'
            "}\n"
            "```\n"
            "Hujjat topilmasa yoki to'lanmagan bo'lsa `{\"valid\": false}` (404)."
        ),
        parameters=[
            OpenApiParameter(
                name='document_id',
                type=int,
                location=OpenApiParameter.PATH,
                description="Sertifikatdagi hujjat ID si",
            ),
        ],
        responses={
            200: OpenApiResponse(description="Sertifikat haqiqiy — ballar bilan"),
            404: OpenApiResponse(description="Sertifikat topilmadi yoki haqiqiy emas"),
        },
    )
    def get(self, request, document_id: int):
        from core.apps.shared.serializers.payment_list import resolve_order_state

        document = (
            Document.objects
            .select_related('user')
            .filter(id=document_id)
            .first()
        )
        if document is None:
            return Response({"valid": False}, status=status.HTTP_404_NOT_FOUND)

        result = document.results.order_by('-id').first()
        order = document.orders.filter(type="document").first()

        if result is None or order is None or resolve_order_state(order) != 'paid':
            return Response({"valid": False}, status=status.HTTP_404_NOT_FOUND)

        res = result.result_json.get("res", {})
        hash_val = res.get("hash", "")
        cert_number = (
            f"{document.id:08d} / {hash_val[:8].upper()}"
            if hash_val else f"{document.id:08d}"
        )
        owner_name = (
            f"{document.user.first_name} {document.user.last_name}".strip()
            or str(document.user.phone)
        )

        return Response({
            "valid": True,
            "document_id": document.id,
            "certificate_number": cert_number,
            "title": document.title,
            "owner_name": owner_name,
            "hash": hash_val,
            "created_at": document.created_at,
            "originality": res.get("originality"),
            "plagiarism": res.get("plagiarism"),
            "citation": res.get("citation"),
            "ai": res.get("ai"),
        })
