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
    create_organization,
)
from core.models import Organization, Project, ProjectContributor


class TestOrganizationMembersAPI(TestCase):
    create_list_view_name = 'organization-member-list-create'
    delete_view_name = 'organization-member-delete'

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = admin_creds.create_user(
          is_active=True,
          is_staff=True
        )
        cls.johndoe_user = johndoe_creds.create_user(is_active=True)
        cls.janedoe_user = janedoe_creds.create_user(is_active=True)
        cls.batman_user = batman_creds.create_user(is_active=True)

    def test_create_with_admin_succeeds(self):
        '''Tests that an admin can add a member to an organization'''
        johndoe_org = create_organization('Org 1', self.johndoe_user)

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.create_list_view_name, kwargs={'org_slug': johndoe_org.slug})

        payload = {'user_id': self.batman_user.id}
        response = admin_client.post(url, payload, format='json')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        data = response.data
        self.assertIn('members', data)

        # john doe and batman are the expected members
        self.assertEqual(2, len(data['members']))

    def test_create_with_org_contact_succeeds(self):
        '''Tests that an org-contact can add a member to their org'''
        johndoe_org = create_organization('Org 1', self.johndoe_user)

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)

        url = reverse(self.create_list_view_name, kwargs={'org_slug': johndoe_org.slug})

        payload = {'user_id': self.batman_user.id}
        response = johndoe_client.post(url, payload, format='json')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        data = response.data
        self.assertIn('members', data)

        # john doe and batman are the expected members
        self.assertEqual(2, len(data['members']))

    def test_create_with_non_admin_non_org_contact_fails(self):
        '''Tests that a non-admin / non-org-contact cannot add member to organization'''
        johndoe_org = create_organization('Org 1', self.johndoe_user)

        janedoe_client = APIClient()
        authenticate_jwt(janedoe_creds, janedoe_client)

        url = reverse(self.create_list_view_name, kwargs={'org_slug': johndoe_org.slug})

        payload = {'user_id': self.batman_user.id}
        response = janedoe_client.post(url, payload, format='json')

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        data = response.data
        self.assertNotIn('members', data)

    def test_delete_by_admin_succeeds(self):
        '''Tests that an admin can delete / remove a member from a organization'''
        johndoe_org = create_organization('Org 1', self.johndoe_user)
        johndoe_org.members.add(self.batman_user)

        project1 = Project.objects.create(
            name='Org 1 Project 1',
            description='ABC ...',
            creator=self.johndoe_user,
            organization=johndoe_org
        )
        project2 = Project.objects.create(
            name='Org 1 Project 2',
            description='ABC ...',
            creator=self.johndoe_user,
            organization=johndoe_org
        )
        ProjectContributor.objects.create(
            user=self.batman_user,
            project=project1
        )
        ProjectContributor.objects.create(
            user=self.batman_user,
            project=project2
        )

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.delete_view_name, kwargs={'org_slug': johndoe_org.slug, 'pk': self.batman_user.id})

        response = admin_client.delete(url, format='json')

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

        johndoe_org.refresh_from_db()
        with self.assertRaises(ObjectDoesNotExist):
            johndoe_org.members.get(id=self.batman_user.id)

        with self.assertRaises(ObjectDoesNotExist):
            ProjectContributor.objects.get(user=self.batman_user, project=project1)

        with self.assertRaises(ObjectDoesNotExist):
            ProjectContributor.objects.get(user=self.batman_user, project=project2)


    def test_delete_by_org_contact_succeeds(self):
        '''Tests that an org contact can delete a member from their org'''
        johndoe_org = create_organization('Org 1', self.johndoe_user)
        johndoe_org.members.add(self.batman_user)

        project1 = Project.objects.create(
            name='Org 1 Project 1',
            description='ABC ...',
            creator=self.johndoe_user,
            organization=johndoe_org
        )
        project2 = Project.objects.create(
            name='Org 1 Project 2',
            description='ABC ...',
            creator=self.johndoe_user,
            organization=johndoe_org
        )
        ProjectContributor.objects.create(
            user=self.batman_user,
            project=project1
        )
        ProjectContributor.objects.create(
            user=self.batman_user,
            project=project2
        )

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)

        url = reverse(self.delete_view_name, kwargs={'org_slug': johndoe_org.slug, 'pk': self.batman_user.id})

        response = johndoe_client.delete(url, format='json')

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

        johndoe_org.refresh_from_db()
        with self.assertRaises(ObjectDoesNotExist):
            johndoe_org.members.get(id=self.batman_user.id)

        with self.assertRaises(ObjectDoesNotExist):
            ProjectContributor.objects.get(user=self.batman_user, project=project1)

        with self.assertRaises(ObjectDoesNotExist):
            ProjectContributor.objects.get(user=self.batman_user, project=project2)


    def test_delete_by_non_admin_non_org_contact_fails(self):
        '''Tests that a non-admin / non-org-contact cannot delete an org's member'''
        johndoe_org = create_organization('Org 1', self.johndoe_user)
        johndoe_org.members.add(self.batman_user)

        project1 = Project.objects.create(
            name='Org 1 Project 1',
            description='ABC ...',
            creator=self.johndoe_user,
            organization=johndoe_org
        )
        project2 = Project.objects.create(
            name='Org 1 Project 2',
            description='ABC ...',
            creator=self.johndoe_user,
            organization=johndoe_org
        )
        ProjectContributor.objects.create(
            user=self.batman_user,
            project=project1
        )
        ProjectContributor.objects.create(
            user=self.batman_user,
            project=project2
        )

        janedoe_client = APIClient()
        authenticate_jwt(janedoe_creds, janedoe_client)

        url = reverse(self.delete_view_name, kwargs={'org_slug': johndoe_org.slug, 'pk': self.batman_user.id})

        response = janedoe_client.delete(url, format='json')

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.assertIsNotNone(johndoe_org.members.get(id=self.batman_user.id))

        self.assertIsNotNone(ProjectContributor.objects.get(project=project1, user=self.batman_user))
        self.assertIsNotNone(ProjectContributor.objects.get(project=project2, user=self.batman_user))
