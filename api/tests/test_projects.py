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
    create_project,
)
from core.models import Organization, Project, ProjectContributor


class TestProjectListAPI(TestCase):
    project_list_view_name = 'projects-list'

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = admin_creds.create_user(
          is_active=True,
          is_staff=True
        )
        cls.johndoe_user = johndoe_creds.create_user(is_active=True)
        cls.janedoe_user = janedoe_creds.create_user(is_active=True)
        cls.batman_user = batman_creds.create_user(is_active=True)

    def test_list_projects_admin_succeed(self):
        '''Tests listing projects by admin returns all projects'''
        org1 = create_organization('Org 1', self.johndoe_user)
        org2 = create_organization('Org 2', self.janedoe_user)

        p1 = create_project('Org 1 Project 1', description='p1', creator=self.johndoe_user, organization=org1)
        p2 = create_project('Org 1 Project 2', description='p2', creator=self.johndoe_user, organization=org1)
        p3 = create_project('Org 2 Project 1', description='p3', creator=self.janedoe_user, organization=org2)

        url = reverse(self.project_list_view_name)
        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        response = admin_client.get(url, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(3, len(response.data))
    
    def test_listing_projects_by_project_contributor_limits_to_theirs_succeed(self):
        '''Tests listing projects by non-admin, project contributor is limited to only those that
        they are a contributor to'''
        org1 = create_organization('Org 1', self.johndoe_user)
        org2 = create_organization('Org 2', self.janedoe_user)

        p1 = create_project('Org 1 Project 1', description='p1', creator=self.johndoe_user, organization=org1)
        p2 = create_project('Org 1 Project 2', description='p2', creator=self.johndoe_user, organization=org1)
        p3 = create_project('Org 2 Project 1', description='p3', creator=self.janedoe_user, organization=org2)

        url = reverse(self.project_list_view_name)
        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)

        response = johndoe_client.get(url, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, len(response.data))

        # make sure project p3 is not in list returned
        self.assertEquals(0, len([p for p in response.data if p['id'] == p3.id]))

    def test_listing_projects_by_non_project_contributor_returns_empty_list_succeeds(self):
        '''Tests that listing projects by non contributor returns empty list'''
        org1 = create_organization('Org 1', self.johndoe_user)
        org2 = create_organization('Org 2', self.janedoe_user)

        p1 = create_project('Org 1 Project 1', description='p1', creator=self.johndoe_user, organization=org1)
        p2 = create_project('Org 1 Project 2', description='p2', creator=self.johndoe_user, organization=org1)
        p3 = create_project('Org 2 Project 1', description='p3', creator=self.janedoe_user, organization=org2)

        batman_client = APIClient()
        authenticate_jwt(batman_creds, batman_client)

        url = url = reverse(self.project_list_view_name)
        response = batman_client.get(url, format='json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(0, len(response.data))


class TestOrganizationProjectAPI(TestCase):
    project_create_list_view_name = 'organization-projects-list-create'
    project_detail_view_name = 'organization-projects-detail'

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = admin_creds.create_user(
          is_active=True,
          is_staff=True
        )
        cls.johndoe_user = johndoe_creds.create_user(is_active=True)
        cls.janedoe_user = janedoe_creds.create_user(is_active=True)


    def test_create_project_with_admin_succeeds(self):
        '''Tests that admin user (is_staff = True) can make project'''
        org = create_organization('Org 1', self.johndoe_user)

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        payload = {
          'name': 'Org 1 Project 1',
          'description': 'A new Project for exercising awesomeness',
        }
        url = reverse(self.project_create_list_view_name, kwargs={
          'org_slug': org.slug
        })
        response = admin_client.post(url, payload, format='json')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        data = response.data
        self.assertIn('name', data)
        self.assertIn('slug', data)
        self.assertIn('description', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('creator', data)
        self.assertIn('organization', data)

        self.assertEqual(payload['name'], data['name'])
        self.assertEqual(payload['description'], data['description'])
        self.assertEqual(org.id, data['organization'])
        self.assertEqual(self.admin_user.id, data['creator'])

        # will raise exception if doesn't exist, no need to assert anything on these lookups
        project = Project.objects.get(slug=data['slug'])
        project_contributor = project.projectcontributor_set.get(project=project, user=self.johndoe_user)

        self.assertTrue(project_contributor.project_admin)

    def test_create_project_with_admin_without_org_fails(self):
        '''Tests that a project being created without an organization fails'''
        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        payload = {
          'name': 'Org 1 Project 1',
          'description': 'A new Project for exercising awesomeness'
        }
        url = reverse(self.project_create_list_view_name, kwargs={'org_slug': 'nope'})
        response = admin_client.post(url, payload, format='json')

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

        data = response.data
        self.assertNotIn('name', data)
        self.assertNotIn('slug', data)
        self.assertNotIn('description', data)
        self.assertNotIn('created_at', data)
        self.assertNotIn('updated_at', data)
        self.assertNotIn('creator', data)

    def test_create_project_by_org_contact_succeeds(self):
        '''Tests that an organization contact can create project for their org'''
        org = create_organization('Org 1', self.johndoe_user)

        client = APIClient()
        authenticate_jwt(johndoe_creds, client)

        payload = {
          'name': 'Org 1 Project 1',
          'description': 'A new Project for exercising awesomeness'
        }
        url = reverse(self.project_create_list_view_name, kwargs={'org_slug': org.slug})
        response = client.post(url, payload, format='json')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        data = response.data
        self.assertIn('name', data)
        self.assertIn('slug', data)
        self.assertIn('description', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('creator', data)
        self.assertIn('organization', data)

        self.assertEqual(payload['name'], data['name'])
        self.assertEqual(payload['description'], data['description'])
        self.assertEqual(org.id, data['organization'])
        self.assertEqual(self.johndoe_user.id, data['creator'])

        # will raise exception if doesn't exist, no need to assert anything on these lookups
        project = Project.objects.get(slug=data['slug'])
        project_contributor = project.projectcontributor_set.get(project=project, user=self.johndoe_user)

        self.assertTrue(project_contributor.project_admin)
    
    def test_create_project_with_non_admin_non_org_contact_fails(self):
        '''Tests that a project cannot be created by a non-admin and non-org-contact'''
        org = create_organization('Org 1', self.johndoe_user)

        janedoe_client = APIClient()
        authenticate_jwt(janedoe_creds, janedoe_client)

        payload = {
          'name': 'Org 1 Project 1',
          'description': 'A new Project for exercising awesomeness'
        }
        url = reverse(self.project_create_list_view_name, kwargs={'org_slug': org.slug})
        response = janedoe_client.post(url, payload, format='json')

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        data = response.data
        self.assertNotIn('name', data)
        self.assertNotIn('slug', data)
        self.assertNotIn('description', data)
        self.assertNotIn('created_at', data)
        self.assertNotIn('updated_at', data)
        self.assertNotIn('creator', data)
        self.assertNotIn('organization', data)

    def test_view_project_with_admin_succeeds(self):
        '''Tests that an admin (is_staff = True) can view project'''
        org = create_organization('Org 1', self.johndoe_user)
        project = create_project(
            'Org 1 Project 1',
            'A new project for exercising awesomeness',
            self.johndoe_user,
            org
        )

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.project_detail_view_name, kwargs={'org_slug':org.slug, 'project_slug': project.slug})
        response = admin_client.get(url, format='json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        data = response.data
        self.assertIn('name', data)
        self.assertIn('slug', data)
        self.assertIn('description', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('creator', data)
        self.assertIn('organization', data)

        self.assertEqual(project.name, data['name'])
        self.assertEqual(project.description, data['description'])
        self.assertEqual(project.slug, data['slug'])
        self.assertEqual(project.creator.id, data['creator'])
        self.assertEqual(project.organization.id, data['organization'])

    def test_view_project_with_org_contact_succeeds(self):
        '''Tests that the organization contact can view project'''
        org = create_organization('Org 1', self.johndoe_user)
        project = create_project(
            'Org 1 Project 1',
            'A new project for exercising awesomeness',
            self.admin_user,
            org
        )

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)

        url = reverse(self.project_detail_view_name, kwargs={'org_slug': org.slug, 'project_slug': project.slug})
        response = johndoe_client.get(url, format='json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        data = response.data
        self.assertIn('name', data)
        self.assertIn('slug', data)
        self.assertIn('description', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('creator', data)
        self.assertIn('organization', data)

        self.assertEqual(project.name, data['name'])
        self.assertEqual(project.description, data['description'])
        self.assertEqual(project.slug, data['slug'])
        self.assertEqual(project.creator.id, data['creator'])
        self.assertEqual(project.organization.id, data['organization'])

    def test_view_project_with_non_admin_non_org_contact_fails(self):
        '''Tests that a project cannot be viewed by non-admin and non-org-contact'''
        org = create_organization('Org 1', self.johndoe_user)
        project = create_project(
            'Org 1 Project 1',
            'A new project for exercising awesomeness',
            self.johndoe_user,
            org
        )

        janedoe_client = APIClient()
        authenticate_jwt(janedoe_creds, janedoe_client)

        url = reverse(self.project_detail_view_name, kwargs={'org_slug': org.slug, 'project_slug': project.slug})
        response = janedoe_client.get(url, format='json')

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        data = response.data
        self.assertNotIn('name', data)
        self.assertNotIn('slug', data)
        self.assertNotIn('description', data)
        self.assertNotIn('created_at', data)
        self.assertNotIn('updated_at', data)
        self.assertNotIn('creator', data)
        self.assertNotIn('organization', data)

    def test_update_project_with_admin_succeeds(self):
        '''Tests that an admin can update a project'''
        org = create_organization('Org 1', self.johndoe_user)
        project = create_project(
            'Org 1 Project 1',
            'A new project for exercising awesomeness',
            self.admin_user,
            org
        )

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        payload = {
          'name': 'Org 1 Project 1 Update',
          'description': 'An updated description'
        }

        url = reverse(self.project_detail_view_name, kwargs={'org_slug': org.slug, 'project_slug': project.slug})
        response = admin_client.put(url, payload, format='json')

        project.refresh_from_db()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        data = response.data
        self.assertIn('name', data)
        self.assertIn('slug', data)
        self.assertIn('description', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('creator', data)
        self.assertIn('organization', data)

        self.assertEqual(project.name, data['name'])
        self.assertEqual(project.description, data['description'])
        self.assertEqual(project.slug, data['slug'])
        self.assertEqual(project.creator.id, data['creator'])
        self.assertEqual(project.organization.id, data['organization'])

    def test_update_project_with_org_contact_succeeds(self):
        '''Tests that an org contact can update an project belonging to their org'''
        org = create_organization('Org 1', self.johndoe_user)
        project = create_project(
            'Org 1 Project 1',
            'A new project for exercising awesomeness',
            self.admin_user,
            org
        )

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)

        payload = {
          'name': 'Org 1 Project 1 Update',
          'description': 'An updated description'
        }

        url = reverse(self.project_detail_view_name, kwargs={'org_slug': org.slug, 'project_slug': project.slug})
        response = johndoe_client.put(url, payload, format='json')

        project.refresh_from_db()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        data = response.data
        self.assertIn('name', data)
        self.assertIn('slug', data)
        self.assertIn('description', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('creator', data)
        self.assertIn('organization', data)

        self.assertEqual(project.name, data['name'])
        self.assertEqual(project.description, data['description'])
        self.assertEqual(project.slug, data['slug'])
        self.assertEqual(project.creator.id, data['creator'])
        self.assertEqual(project.organization.id, data['organization'])

    def test_update_project_with_non_admin_non_org_contact_fails(self):
        '''Tests that a project cannot be updated by non-admin and non-org-contact'''
        org = create_organization('Org 1', self.johndoe_user)
        project = create_project(
            'Org 1 Project 1',
            'A new project for exercising awesomeness',
            self.johndoe_user,
            org
        )

        janedoe_client = APIClient()
        authenticate_jwt(janedoe_creds, janedoe_client)

        payload = {
          'name': 'Org 1 Project 1 Update',
          'description': 'An updated description'
        }

        url = reverse(self.project_detail_view_name, kwargs={'org_slug': org.slug, 'project_slug': project.slug})
        response = janedoe_client.put(url, payload, format='json')

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        data = response.data
        self.assertNotIn('name', data)
        self.assertNotIn('slug', data)
        self.assertNotIn('description', data)
        self.assertNotIn('created_at', data)
        self.assertNotIn('updated_at', data)
        self.assertNotIn('creator', data)
        self.assertNotIn('organization', data)

    def test_delete_project_with_admin_succeeds(self):
        '''Tests that an admin can delete a project'''
        org = create_organization('Org 1', self.johndoe_user)
        project = create_project(
            'Org 1 Project 1',
            'A new project for exercising awesomeness',
            self.johndoe_user,
            org
        )

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        slug = project.slug
        url = reverse(self.project_detail_view_name, kwargs={'org_slug': org.slug, 'project_slug': project.slug})
        response = admin_client.delete(url, format='json')

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        with self.assertRaises(ObjectDoesNotExist):
            Project.objects.get(slug=slug)

    def test_delete_project_with_non_admin_fails(self):
        '''Tests that a project can only be deleted by an admin'''
        org = create_organization('Org 1', self.johndoe_user)
        project = create_project(
            'Org 1 Project 1',
            'A new project for exercising awesomeness',
            self.johndoe_user,
            org
        )

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)

        slug = project.slug
        url = reverse(self.project_detail_view_name, kwargs={'org_slug': org.slug, 'project_slug': project.slug})
        response = johndoe_client.delete(url, format='json')

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.assertIsNotNone(Project.objects.get(slug=slug))

