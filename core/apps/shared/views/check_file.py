from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from core.apps.shared.utils.check_file import extract_text
from core.apps.shared.serializers.check_file import CheckFileSerializer


class CheckFileView(GenericAPIView):
    serializer_class = CheckFileSerializer
    permission_classes = []

    @extend_schema(
        description="Bu api bilan siz yuborilgan filedagi umumiy so'zlar sonini va shu file uchun narxini qaytaradi."
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
