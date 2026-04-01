from django.contrib.auth import get_user_model

from rest_framework import generics, status
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from core.apps.users.serializers.register import RegisterSerializer

User = get_user_model()


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
