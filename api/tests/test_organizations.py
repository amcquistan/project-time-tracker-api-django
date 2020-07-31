from copy import deepcopy

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from api.tests.testing_utils import (
    create_user,
    authenticate_jwt,
    admin_creds,
    johndoe_creds,
    janedoe_creds,
    batman_creds,
)
from core.models import Organization


class TestOrganizationAPI(TestCase):
    create_list_view_name = 'organization-list-create'
    detail_view_name = 'organization-detail'

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = admin_creds.create_user(
          is_active=True,
          is_staff=True
        )
        cls.johndoe_user = johndoe_creds.create_user(is_active=True)
        cls.janedoe_user = janedoe_creds.create_user(is_active=True)
        cls.batman_user = batman_creds.create_user(is_active=True)

    def test_create_organization_with_admin_user_succeeds(self):
        '''Tests that admin user (is_staff = True) can create organization'''
        client = APIClient()
        authenticate_jwt(admin_creds, client)

        url = reverse(self.create_list_view_name)
        payload = {
          'name': 'Org1',
          'contact': self.johndoe_user.id
        }
        response = client.post(url, payload, format='json')
        
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        
        data = response.data
        self.assertIn('name', data)
        self.assertIn('slug', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('contact', data)

        self.assertEqual(payload['name'], data['name'])
        self.assertEqual(payload['contact'], data['contact'])
        self.assertEqual(1, len(data['members']))

    def test_create_organization_with_non_admin_user_fails(self):
        '''Tests that non admin user (is_staff = False) cannot create organization'''
        client = APIClient()
        authenticate_jwt(johndoe_creds, client)

        url = reverse(self.create_list_view_name)
        payload = { 'name': 'Org1', 'contact': self.johndoe_user.id }
        response = client.post(url, payload, format='json')

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        
        data = response.data
        self.assertNotIn('name', data)
        self.assertNotIn('slug', data)
        self.assertNotIn('created_at', data)
        self.assertNotIn('updated_at', data)
        self.assertNotIn('contact', data)

    def test_list_organization_with_admin_user_succeeds(self):
        '''Tests that admin user (is_staff = True) can view organization listing'''
        client = APIClient()
        authenticate_jwt(admin_creds, client)

        url = reverse(self.create_list_view_name)
        payload = { 'name': 'Org1', 'contact': self.johndoe_user.id }
        client.post(url, payload, format='json')

        payload2 = { 'name': 'Org2', 'contact': self.janedoe_user.id }
        client.post(url, payload2, format='json')

        response = client.get(url, format='json')
        
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIsInstance(data, list)
        self.assertEqual(2, len(data))

    def test_list_organization_with_org_contact_succeeds(self):
        '''Tests that an organization contact can view the listing API but,
        only their org's come back'''
        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.create_list_view_name)
        payload = { 'name': 'Org1', 'contact': self.johndoe_user.id }
        admin_client.post(url, payload, format='json')

        payload2 = { 'name': 'Org2', 'contact': self.janedoe_user.id }
        admin_client.post(url, payload2, format='json')

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)

        response = johndoe_client.get(url, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIsInstance(data, list)
        self.assertEqual(1, len(data))
    
    def test_list_organization_with_non_admin_user_fails(self):
        '''Tests that non admin user (is_staff = False) cannot view organization listing'''
        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.create_list_view_name)
        payload = { 'name': 'Org1', 'contact': self.johndoe_user.id }
        admin_client.post(url, payload, format='json')

        payload2 = { 'name': 'Org2', 'contact': self.johndoe_user.id }
        admin_client.post(url, payload2, format='json')

        janedoe_client = APIClient()
        authenticate_jwt(janedoe_creds, janedoe_client)

        response = janedoe_client.get(url, format='json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        data = response.data
        self.assertFalse(isinstance(data, list))

    def test_view_organization_with_admin_user_succeeds(self):
        '''Tests that admin user (is_staff = True) can view orgnaization details'''
        client = APIClient()
        authenticate_jwt(admin_creds, client)

        payload = { 'name': 'Org1', 'contact': self.johndoe_user.id }
        create_response = client.post(reverse(self.create_list_view_name), payload, format='json')
        slug = create_response.data['slug']
        url = reverse(self.detail_view_name, kwargs={'org_slug': slug})

        response = client.get(url, format='json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIn('name', data)
        self.assertIn('slug', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('contact', data)

        self.assertEqual(payload['name'], data['name'])
        self.assertEqual(payload['contact'], data['contact'])
    
    def test_view_organization_with_org_contact_succeeds(self):
        '''Tests that organization contact can view the details of organization'''
        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        payload = { 'name': 'Org1', 'contact': self.johndoe_user.id }
        create_response = admin_client.post(reverse(self.create_list_view_name), payload, format='json')
        slug = create_response.data['slug']
        url = reverse(self.detail_view_name, kwargs={'org_slug': slug})

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)
        response = johndoe_client.get(url, format='json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIn('name', data)
        self.assertIn('slug', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('contact', data)

        self.assertEqual(payload['name'], data['name'])
        self.assertEqual(payload['contact'], data['contact'])

    def test_view_organization_with_non_admin_user_fails(self):
        '''Tests that non admin user (is_staff = False) cannot view organization details'''
        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        payload = { 'name': 'Org1', 'contact': self.johndoe_user.id }
        create_response = admin_client.post(reverse(self.create_list_view_name), payload, format='json')
        slug = create_response.data['slug']
        url = reverse(self.detail_view_name, kwargs={'org_slug': slug})

        janedoe_client = APIClient()

        authenticate_jwt(janedoe_creds, janedoe_client)
        response = janedoe_client.get(url, format='json')

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        data = response.data
        self.assertNotIn('name', data)
        self.assertNotIn('slug', data)
        self.assertNotIn('created_at', data)
        self.assertNotIn('updated_at', data)
        self.assertNotIn('contact', data)

    def test_update_organization_with_admin_succeeds(self):
        '''Tests that admin (is_staff = True) can update organization'''
        client = APIClient()
        authenticate_jwt(admin_creds, client)

        payload = { 'name': 'Org1', 'contact': self.johndoe_user.id }
        create_response = client.post(reverse(self.create_list_view_name), payload, format='json')
        slug = create_response.data['slug']
        url = reverse(self.detail_view_name, kwargs={'org_slug': slug})

        updated_payload = deepcopy(payload)
        updated_payload['contact'] = self.janedoe_user.id
        updated_payload['name'] = 'Updated Org'
        response = client.put(url, updated_payload, format='json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIn('name', data)
        self.assertIn('slug', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('contact', data)

        self.assertEqual(updated_payload['name'], data['name'])
        self.assertEqual(updated_payload['contact'], data['contact'])
    
    def test_update_organization_with_organization_contact_succeeds(self):
        '''Tests that an org contact can update their organization'''
        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        payload = { 'name': 'Org1', 'contact': self.johndoe_user.id }
        create_response = admin_client.post(reverse(self.create_list_view_name), payload, format='json')
        slug = create_response.data['slug']
        url = reverse(self.detail_view_name, kwargs={'org_slug': slug})

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)
        updated_payload = deepcopy(payload)
        updated_payload['name'] = 'Updated Org'
        response = johndoe_client.put(url, updated_payload, format='json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIn('name', data)
        self.assertIn('slug', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('contact', data)

        self.assertEqual(updated_payload['name'], data['name'])
        self.assertEqual(updated_payload['contact'], data['contact'])
    
    # def test_update_organization_with_org_contact_change_contact_fails(self):
    #     '''Tests that an organization contact cannot udpate org's contact to someone else'''
    #     admin_client = APIClient()
    #     authenticate_jwt(admin_creds, admin_client)

    #     payload = { 'name': 'Org1', 'contact': self.johndoe_user.id }
    #     create_response = admin_client.post(reverse(self.create_list_view_name), payload, format='json')
    #     slug = create_response.data['slug']
    #     url = reverse(self.detail_view_name, kwargs={'org_slug': slug})

    #     johndoe_client = APIClient()
    #     authenticate_jwt(johndoe_creds, johndoe_client)
    #     updated_payload = deepcopy(payload)
    #     updated_payload['name'] = 'Updated Org'
    #     updated_payload['contact'] = self.janedoe_user.id
    #     response = johndoe_client.put(url, updated_payload, format='json')

    #     self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    #     data = response.data
    #     self.assertNotIn('name', data)
    #     self.assertNotIn('slug', data)
    #     self.assertNotIn('created_at', data)
    #     self.assertNotIn('updated_at', data)
    #     self.assertNotIn('contact', data)

    def test_update_organization_with_non_admin_non_contact_fails(self):
        '''Tests that a user who is not an admin (is_staff = False) and also
        not organization contact cannot update an organization'''
        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        payload = { 'name': 'Org1', 'contact': self.janedoe_user.id }
        create_response = admin_client.post(reverse(self.create_list_view_name), payload, format='json')
        slug = create_response.data['slug']
        url = reverse(self.detail_view_name, kwargs={'org_slug': slug})

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)
        updated_payload = deepcopy(payload)
        updated_payload['name'] = 'Updated Org'
        updated_payload['contact'] = self.janedoe_user.id
        response = johndoe_client.put(url, updated_payload, format='json')

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        data = response.data
        self.assertNotIn('name', data)
        self.assertNotIn('slug', data)
        self.assertNotIn('created_at', data)
        self.assertNotIn('updated_at', data)
        self.assertNotIn('contact', data)

    def test_delete_organization_with_admin_succeeds(self):
        '''Tests that a admin (is_staff = True) can delete an organization'''
        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        payload = { 'name': 'Org1', 'contact': self.janedoe_user.id }
        create_response = admin_client.post(reverse(self.create_list_view_name), payload, format='json')
        slug = create_response.data['slug']
        url = reverse(self.detail_view_name, kwargs={'org_slug': slug})

        response = admin_client.delete(url, format='json')
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

        with self.assertRaises(ObjectDoesNotExist):
            Organization.objects.get(slug=slug)

    def test_delete_organization_with_non_admin_fails(self):
        '''Tests that a non-admin (is_staff = False) cannot delete an organization,
        note that this is different from other mutations which allow organization contact
        to make changes'''
        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        payload = { 'name': 'Org1', 'contact': self.janedoe_user.id }
        create_response = admin_client.post(reverse(self.create_list_view_name), payload, format='json')
        slug = create_response.data['slug']
        url = reverse(self.detail_view_name, kwargs={'org_slug': slug})

        janedoe_client = APIClient()
        authenticate_jwt(janedoe_creds, janedoe_client)

        response = janedoe_client.delete(url, format='json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.assertIsNotNone(Organization.objects.get(slug=slug))
