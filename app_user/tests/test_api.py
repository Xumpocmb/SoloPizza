from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

User = get_user_model()

class UserAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )
        # Добавляем номер телефона для тестового пользователя
        self.user.phone = '+79001234567'
        self.user.save()
        
        self.user.address = 'ул. Тестовая, д. 1, кв. 42, этаж 4, подъезд 2'
        self.user.save()
        
    def test_user_registration(self):
        """Тест регистрации нового пользователя по номеру телефона"""
        url = reverse('user_register')
        data = {
            'phone': '+79001234568',
            'password': 'newpassword123',
            'password2': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        # Проверяем, что пользователь создан с указанным номером телефона
        new_user = User.objects.get(phone='+79001234568')
        self.assertIsNotNone(new_user)
    
    def test_user_registration_password_mismatch(self):
        """Тест регистрации с несовпадающими паролями"""
        url = reverse('user_register')
        data = {
            'phone': '+79001234568',
            'password': 'newpassword123',
            'password2': 'differentpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)  # Пользователь не должен быть создан
        
    def test_user_registration_duplicate_phone(self):
        """Тест регистрации с уже существующим номером телефона"""
        url = reverse('user_register')
        data = {
            'phone': '+79001234567',  # Номер телефона, который уже используется
            'password': 'newpassword123',
            'password2': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)  # Пользователь не должен быть создан
    
    def test_token_obtain(self):
        """Тест получения JWT токена"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
    def test_user_login_with_phone(self):
        """Тест авторизации по номеру телефона и паролю"""
        url = reverse('user_login')
        data = {
            'phone': '+79001234567',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user_id', response.data)
        self.assertEqual(response.data['phone'], '+79001234567')
        
    def test_user_login_with_invalid_credentials(self):
        """Тест авторизации с неверными учетными данными"""
        url = reverse('user_login')
        data = {
            'phone': '+79001234567',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_user_login_with_nonexistent_phone(self):
        """Тест авторизации с несуществующим номером телефона"""
        url = reverse('user_login')
        data = {
            'phone': '+79009876543',  # Несуществующий номер телефона
            'password': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_token_refresh(self):
        """Тест обновления JWT токена"""
        # Сначала получаем токены
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        refresh_token = response.data['refresh']
        
        # Теперь обновляем токен
        url = reverse('token_refresh')
        data = {'refresh': refresh_token}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_user_profile_unauthorized(self):
        """Тест доступа к профилю без авторизации"""
        url = reverse('user_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_profile_get(self):
        """Тест получения данных профиля"""
        url = reverse('user_profile')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['phone'], '+79001234567')
        self.assertEqual(response.data['address'], 'ул. Тестовая, д. 1, кв. 42, этаж 4, подъезд 2')
    
    def test_user_profile_update(self):
        """Тест обновления данных профиля"""
        url = reverse('user_profile')
        self.client.force_authenticate(user=self.user)
        data = {
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '+79009876543',
            'address': 'ул. Новая, д. 5, кв. 10'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем, что данные обновились
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.phone, '+79009876543')
        self.assertEqual(self.user.address, 'ул. Новая, д. 5, кв. 10')
