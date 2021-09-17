from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

# Constante de URL para crear usuario
CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

def create_user(**params):
    return get_user_model().objects.create_user(**params)

class PublicUserApiTest(TestCase):
    # Testea el API Publico del usuario
    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        # Test para crear usuario con un payload exitoso.
        payload = {
            'email':'test@gmail.com',
            'password':'testpass123',
            'name':'TestName'
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)
    
    def test_user_exists(self):
        # Probar un usuario que ya exista falla

        payload = {
            'email':'test@gmail.com',
            'password':'testpass123',
            'name':'TestName'
        }
        create_user(**payload)

        res= self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        # Test para contraseña muy corta, debe ser mayor a 8 caracteres
        payload = {
            'email':'test@gmail.com',
            'password':'pw',
            'name':'TestName'
        }
        res= self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(email = payload['email']).exists()
        self.assertFalse(user_exists)
#============================================================================================
#                                        Token User       
#============================================================================================
    def test_create_token_for_user(self):
        # Probar que el token sea creado para el usuario
        payload = {'email':'test@gmail.com', 'password':'testpass123', 'name':'TestName'}
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
#============================================================================================
    def test_create_token_invalid_credentials(self):
        # Test para validar que el token no es creado con credenciales invalidas
        create_user(email='test@gmail.com', password='testpass123', name = 'TestName')
        payload = {'email':'test@gmail.com','password':'wrong'}
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    #============================================================================================
    def test_create_token_no_user(self):
        # Test para no crear token si no hay usuario
        payload = {'email':'test@gmail.com','password':'testpass456','name':'TestName'}
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    #============================================================================================
    def test_create_token_missing_field(self):
        # Test para no crear token si no hay contraseña o email
        res = self.client.post(TOKEN_URL, {'email':'one','password':''})
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    #=========================== Verificacion de Usuario ========================================
    #============================================================================================
    def test_retrieve_user_unauthorized(self):
        # Prueba que la authentication sea requerida para los usuarios
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

#==================================Private UsercAPI Test =======================================
class PrivateUserApiTest(TestCase):
    # Testear el API Privado del usuario
    def setUp(self):
        self.user = create_user(
            email = 'test@gmail.com',
            password='testpass123',
            name='name'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    def test_retrieve_profile_success(self):
        # Probar obtener perfil para usuario
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email':self.user.email
        })

    def test_post_me_not_allowed(self):
        # Prueba que el Post no sea permitido
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        # Probar que el perfil esta siendo actualizado si esta autenticado
        payload = {'email':'test@gmail.com', 'password':'testpass123', 'name':'new name'}
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email, (payload['email']))
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(self.user.name, payload['name'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)
