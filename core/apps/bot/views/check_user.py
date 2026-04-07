from rest_framework import views, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from core.apps.users.models import User


class CheckUserView(views.APIView):
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
            access_token = str(token.access_token)
            refresh_token = str(token)

            return Response(
                {
                    "success": True,
                    "message": "User found",
                    "data": {
                        "token": {
                            "access": access_token,
                            "refresh": refresh_token,
                        },
                        "user": {
                            "id": user.id,
                            "tg_id": user.tg_id,
                        }
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
