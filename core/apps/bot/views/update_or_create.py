from django.db import transaction

from rest_framework import generics, status
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from core.apps.bot.serializers.update_user import BotUserSerializer
from core.apps.users.models import User


class UpdateUserView(generics.GenericAPIView):
    serializer_class = BotUserSerializer
    permission_classes = []
    queryset = User.objects.all()

    @transaction.atomic
    def post(self, request):
        try:
            serializer = BotUserSerializer(data=request.data)
            if serializer.is_valid():
                # checking data
                data = serializer.validated_data

                # getting validated data from serializer
                first_name = data.get('first_name')
                last_name = data.get('last_name')
                tg_id = data.get('tg_id')
                phone = data.get('phone')

                # creating new user
                user, created = User.objects.update_or_create(
                    phone=phone,
                    defaults={'first_name': first_name, 'last_name': last_name, 'tg_id': tg_id}
                )

                token = RefreshToken.for_user(user)
                # token
                access_token = str(token.access_token)
                refresh_token = str(token)
                # lifetime
                access_lifetime = str(token.access_token.lifetime)
                refresh_lifetime = str(token.lifetime)

                return Response(
                    {
                        "success": True,
                        "message": "User updated successfully" if not created else "User created successfully",
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
                        },
                        "errors": {}
                    },
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {
                    "success": False,
                    "message": "Invalid data",
                    "data": {},
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": "Internal server error",
                    "data": {},
                    "errors": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
