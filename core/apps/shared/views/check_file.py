from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiResponse

from core.apps.shared.utils.check_file import extract_text
from core.apps.shared.serializers.check_file import CheckFileSerializer


class CheckFileView(GenericAPIView):
    serializer_class = CheckFileSerializer
    permission_classes = []

    @extend_schema(
        tags=['Check File'],
        summary="Fayl narxini oldindan hisoblash",
        description=(
            "Yuborilgan fayldagi belgilar sonini va tekshiruv narxini qaytaradi. "
            "**Auth talab qilinmaydi** — hujjat yaratishdan oldin foydalanuvchiga "
            "narxni ko'rsatish uchun ishlatiladi.\n\n"
            "So'rov `multipart/form-data` formatida, `file` maydoni bilan yuboriladi.\n\n"
            "**Javob (200):**\n"
            "```json\n"
            '{ "total_price": 25000, "word_count": 5000 }\n'
            "```\n"
            "Narx: 1 belgi = 5 so'm, minimal narx 10 000 so'm."
        ),
        responses={
            200: OpenApiResponse(description="Narx va belgilar soni"),
            400: OpenApiResponse(description="Fayl yuborilmagan yoki format noto'g'ri"),
        },
    )
    def post(self, request):
        serializer = CheckFileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        text = extract_text(serializer.validated_data['file'])
        txt_count = len(text)
        total_price = txt_count * 5
        if total_price < 10000:
            total_price = 10000.00

        return Response(
            {
                "total_price": total_price,
                "word_count": txt_count,
            }
        )
