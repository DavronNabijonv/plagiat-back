from rest_framework_simplejwt.views import TokenObtainPairView

from drf_spectacular.utils import extend_schema, OpenApiResponse

from core.apps.users.serializers.login import CustomTokenObtainPairSerializer


@extend_schema(
    tags=['Auth'],
    summary="Login (JWT token olish)",
    description=(
        "Telefon raqam va parol orqali tizimga kirish. Muvaffaqiyatli bo'lsa "
        "JWT tokenlar va foydalanuvchi ma'lumotlari qaytariladi.\n\n"
        "**So'rov maydonlari:**\n"
        "- `phone` — ro'yxatdan o'tilgan telefon raqam\n"
        "- `password` — parol\n\n"
        "**Muvaffaqiyatli javob (200):**\n"
        "```json\n"
        "{\n"
        '  "refresh": "<refresh_token>",\n'
        '  "access": "<access_token>",\n'
        '  "user_id": 1,\n'
        '  "phone": "+998901234567",\n'
        '  "first_name": "Ali",\n'
        '  "last_name": "Valiyev"\n'
        "}\n"
        "```\n"
        "`access` tokenni himoyalangan endpointlarda `Authorization: Bearer <access>` "
        "header'ida yuboring."
    ),
    responses={
        200: OpenApiResponse(description="Login muvaffaqiyatli, tokenlar qaytariladi"),
        401: OpenApiResponse(description="Telefon raqam yoki parol noto'g'ri"),
    },
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
