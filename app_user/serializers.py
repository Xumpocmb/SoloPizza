from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
import random
import string
import uuid

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации новых пользователей"""
    phone = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('phone', 'password', 'password2')
    
    def validate(self, attrs):
        # Проверяем, что номер телефона не занят
        phone = attrs.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError({"phone": "Пользователь с таким номером телефона уже существует."})
            
        # Проверяем совпадение паролей
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
            
        # Валидация пароля
        validate_password(attrs['password'])
        
        return attrs
    
    def create(self, validated_data):
        phone = validated_data.get('phone')
        password = validated_data.get('password')
        
        # Удаляем password2, так как он нам больше не нужен
        validated_data.pop('password2', None)
        
        # Генерируем случайные данные для остальных полей
        username = f"user_{uuid.uuid4().hex[:8]}"
        email = f"{username}@example.com"
        first_name = "Пользователь"
        last_name = str(random.randint(10000, 99999))
        
        # Создаем пользователя
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Сохраняем номер телефона
        user.phone = phone
        user.save()
        
        return user

class UserLoginSerializer(serializers.Serializer):
    """Сериализатор для авторизации пользователя по номеру телефона и паролю"""
    phone = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        phone = attrs.get('phone')
        password = attrs.get('password')
        
        if phone and password:
            user = authenticate(request=self.context.get('request'), phone=phone, password=password)
            
            if not user:
                msg = 'Невозможно авторизоваться с предоставленными учетными данными.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Необходимо указать номер телефона и пароль.'
            raise serializers.ValidationError(msg, code='authorization')
        
        attrs['user'] = user
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра и обновления профиля пользователя"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone', 'address')
        read_only_fields = ('id', 'username')
