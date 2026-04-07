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
        description="User profile update qilish uchun api, foydalanuvchi faqat o'zini ma'lumotlarini update qilishi mumkin"
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
        description="User profile ma'lumotlarini olish uchun api, foydalanuvchi faqat o'zini ma'lumotlarini olishi mumkin"
    )
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        