from django.contrib.auth import get_user_model

from rest_framework import generics, status
from rest_framework.response import Response

from core.apps.users.serializers.register import RegisterSerializer

User = get_user_model()


class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"detail": "Ro'yxatdan o'tish muvaffaqiyatli amalga oshirildi."},
            status=status.HTTP_201_CREATED
        )
