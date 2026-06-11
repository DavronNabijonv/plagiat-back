from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from core.apps.users.serializers.user import UserSerializer
from core.apps.users.models import User


class UserProfileView(GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    
    @extend_schema(
        tags=['Profile'],
        summary="Profilni tahrirlash",
        description=(
            "Foydalanuvchi o'z profil ma'lumotlarini qisman yangilaydi (PATCH — "
            "faqat o'zgartirmoqchi bo'lgan maydonlarni yuborish kifoya). "
            "Foydalanuvchi faqat o'z ma'lumotlarini o'zgartira oladi.\n\n"
            "**Auth:** `Authorization: Bearer <access>` majburiy.\n\n"
            "Muvaffaqiyatli javobda yangilangan profil qaytariladi."
        ),
    )
    def patch(self, request, *args, **kwargs):
        try:
            user = request.user
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    @extend_schema(
        tags=['Profile'],
        summary="Profil ma'lumotlarini olish",
        description=(
            "Joriy (token egasi) foydalanuvchining profil ma'lumotlarini qaytaradi. "
            "Foydalanuvchi faqat o'z ma'lumotlarini ko'ra oladi.\n\n"
            "**Auth:** `Authorization: Bearer <access>` majburiy."
        ),
    )
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        