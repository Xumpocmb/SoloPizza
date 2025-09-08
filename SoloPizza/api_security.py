from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.permissions import BasePermission

# Ограничение запросов для авторизованных пользователей
class UserThrottle(UserRateThrottle):
    rate = '100/minute'

# Ограничение запросов для неавторизованных пользователей
class AnonThrottle(AnonRateThrottle):
    rate = '20/minute'

# Пользовательское разрешение для API
class IsOwnerOrReadOnly(BasePermission):
    """
    Разрешение, которое позволяет только владельцам объекта редактировать его.
    """
    
    def has_object_permission(self, request, view, obj):
        # Разрешаем GET, HEAD или OPTIONS запросы
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
            
        # Проверяем, является ли пользователь владельцем объекта
        return obj.user == request.user