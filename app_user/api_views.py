from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model, login
from rest_framework.authtoken.models import Token
import logging
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserLoginSerializer,
)

# Получаем логгер для мобильной регистрации
mobile_logger = logging.getLogger('app_user.mobile')

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    """API endpoint для регистрации новых пользователей"""
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        # Логируем входящие данные от мобильного приложения
        mobile_logger.info(f"Получен запрос на регистрацию: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            # Логируем ошибки валидации
            mobile_logger.error(f"Ошибка валидации данных: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            # Логируем успешную регистрацию
            mobile_logger.info(f"Пользователь успешно зарегистрирован: {serializer.data}")
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            # Логируем непредвиденные ошибки
            mobile_logger.error(f"Ошибка при регистрации пользователя: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserLoginView(APIView):
    """API endpoint для авторизации пользователя по номеру телефона и паролю"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        # Логируем входящие данные авторизации
        mobile_logger.info(f"Получен запрос на авторизацию: {request.data}")
        
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            # Логируем успешную авторизацию
            mobile_logger.info(f"Пользователь успешно авторизован: user_id={user.pk}, phone={user.phone}")
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'phone': user.phone
            })
        # Логируем ошибки авторизации
        mobile_logger.error(f"Ошибка авторизации: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """API endpoint для просмотра и обновления профиля пользователя"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        return self.request.user
