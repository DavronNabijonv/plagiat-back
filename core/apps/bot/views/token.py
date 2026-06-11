from django.db import transaction

from rest_framework import views, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)

from core.apps.users.models import User


class TokenView(views.APIView):
    @extend_schema(
        tags=['Bot'],
        summary="Telegram ID bo'yicha JWT token olish (bot uchun)",
        description=(
            "Telegram bot foydalanuvchisi uchun JWT tokenlar qaytaradi. "
            "Asosan Telegram bot backend'i ishlatadi.\n\n"
            "**Javob (200):**\n"
            "```json\n"
            "{\n"
            '  "success": true,\n'
            '  "message": "User found",\n'
            '  "data": {\n'
            '    "user": { "id": 1, "tg_id": "123456789" },\n'
            '    "tokens": {\n'
            '      "access":  { "token": "<jwt>", "lifetime": 86400 },\n'
            '      "refresh": { "token": "<jwt>", "lifetime": 604800 }\n'
            "    }\n"
            "  }\n"
            "}\n"
            "```\n"
            "`lifetime` — sekundlarda."
        ),
        parameters=[
            OpenApiParameter(
                name='tg_id',
                type=str,
                location=OpenApiParameter.PATH,
                description="Foydalanuvchining Telegram ID si",
            ),
        ],
        responses={
            200: OpenApiResponse(description="Foydalanuvchi topildi, tokenlar qaytarildi"),
            404: OpenApiResponse(description="Bunday tg_id li foydalanuvchi topilmadi"),
        },
    )
    @transaction.atomic
    def get(self, request, tg_id):
        try:
            user = User.objects.filter(tg_id=tg_id).first()
            if not user:
                return Response(
                    {
                        "success": False,
                        "message": "User not found",
                        "data": {},
                        "errors": "",
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            token = RefreshToken.for_user(user)
            # token
            access_token = str(token.access_token)
            refresh_token = str(token)
            # lifetime
            access_lifetime = int(token.access_token.lifetime.total_seconds())
            refresh_lifetime = int(token.lifetime.total_seconds())

            return Response(
                {
                    "success": True,
                    "message": "User found",
                    "data": {
                        "user": {
                            "id": user.id,
                            "tg_id": user.tg_id,
                        },
                        "tokens": {
                            "access": {
                                "token": access_token,
                                "lifetime": access_lifetime,
                            },
                            "refresh": {
                                "token": refresh_token,
                                "lifetime": refresh_lifetime,
                            },
                        },
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": "Internal server error",
                    "data": {},
                    "errors": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
