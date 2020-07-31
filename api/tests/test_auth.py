from django.shortcuts import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from api.tests.testing_utils import (
    create_user,
    authenticate_jwt,
    admin_creds
)


class TestAuthAPI(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = admin_creds.create_user(
          is_active=True,
          is_staff=True
        )

    def setUp(self):
        self.client = APIClient()

    def test_login_success(self):
        response = authenticate_jwt(admin_creds, self.client)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data

        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
        self.assertIn('user', data)
        self.assertEqual(admin_creds.email, data['user']['email'])

    def test_login_no_password_fail(self):
        creds = admin_creds.to_dict()
        creds.pop('password')
        response = authenticate_jwt(creds, self.client)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        data = response.data

        self.assertNotIn('access_token', data)
        self.assertNotIn('refresh_token', data)
      
    def test_login_incorrect_password_fail(self):
        creds = admin_creds.to_dict()
        creds['password'] = 'WRONG!'
        response = authenticate_jwt(creds, self.client)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        data = response.data

        self.assertNotIn('access_token', data)
        self.assertNotIn('refresh_token', data)

    def test_login_user_not_exists_fail(self):
        creds = admin_creds.to_dict()
        creds['email'] = 'YOUWILLNEVERFINDME@MAIL.com'
        response = authenticate_jwt(creds, self.client)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        data = response.data

        self.assertNotIn('access_token', data)
        self.assertNotIn('refresh_token', data)

    def test_user_detail_auth_required_success(self):
        auth_response = authenticate_jwt(admin_creds, self.client)

        url = reverse('rest_user_details')
        client = APIClient()

        client.credentials(HTTP_AUTHORIZATION=f"Bearer {auth_response.data['access_token']}")

        response = client.get(url, data={'format': 'json'})
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data

        self.assertIn('email', data)
        self.assertIn('name', data)
        self.assertIn('phone_number', data)
        self.assertIn('is_staff', data)
        self.assertIn('is_superuser', data)

    def test_user_detail_auth_required_fail(self):
        url = reverse('rest_user_details')
        client = APIClient()

        client.credentials(HTTP_AUTHORIZATION=f"Bearer not-a-valid-token")

        response = client.get(url, data={'format': 'json'})
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        data = response.data

        self.assertNotIn('email', data)
        self.assertNotIn('name', data)
        self.assertNotIn('phone_number', data)
        self.assertNotIn('is_staff', data)
        self.assertNotIn('is_superuser', data)
