from django.contrib.auth import get_user_model

from rest_framework import generics, status
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema, OpenApiResponse

from core.apps.users.serializers.register import RegisterSerializer

User = get_user_model()


@extend_schema(
    tags=['Auth'],
    summary="Ro'yxatdan o'tish",
    description=(
        "Yangi foydalanuvchini ro'yxatdan o'tkazadi va darhol JWT tokenlar qaytaradi — "
        "qo'shimcha login qilish shart emas.\n\n"
        "**So'rov maydonlari:**\n"
        "- `phone` — telefon raqam (login sifatida ishlatiladi, unikal)\n"
        "- `first_name` — ism\n"
        "- `last_name` — familiya\n"
        "- `password` — parol (kamida 8 ta belgi)\n\n"
        "**Muvaffaqiyatli javob (201):**\n"
        "```json\n"
        "{\n"
        '  "detail": "Ro\'yxatdan o\'tish muvaffaqiyatli amalga oshirildi.",\n'
        '  "refresh": "<refresh_token>",\n'
        '  "access": "<access_token>",\n'
        '  "user_id": 1,\n'
        '  "first_name": "Ali",\n'
        '  "last_name": "Valiyev"\n'
        "}\n"
        "```\n"
        "`access` tokenni keyingi so'rovlarda `Authorization: Bearer <access>` "
        "header'ida yuboring."
    ),
    responses={
        201: OpenApiResponse(description="Ro'yxatdan o'tish muvaffaqiyatli, tokenlar qaytariladi"),
        400: OpenApiResponse(description="Validatsiya xatosi (telefon band, parol qisqa va h.k.)"),
    },
)
class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = RefreshToken.for_user(user)
        refresh = str(token)
        access = str(token.access_token)
        return Response(
            {"detail": "Ro'yxatdan o'tish muvaffaqiyatli amalga oshirildi.", "refresh": refresh, "access": access, "user_id": user.id, "first_name": user.first_name, "last_name": user.last_name},
            status=status.HTTP_201_CREATED
        )
