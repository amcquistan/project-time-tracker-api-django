from copy import deepcopy

from django.contrib.auth import get_user_model
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


UserModel = get_user_model()


class TestProjectContributorAPI(TestCase):
    list_create_view_name = 'project-contributor-list-create'
    detail_view_name = 'project-contributor-detail'

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = admin_creds.create_user(
          is_active=True,
          is_staff=True
        )
        cls.johndoe_user = johndoe_creds.create_user(is_active=True)
        cls.janedoe_user = janedoe_creds.create_user(is_active=True)

    def test_create_non_existant_user_contributor_by_admin_succeeds(self):
        '''Tests that admin (is_staff = True) can add a project contributor,
        which does not match to an existing user, to a project. 
        - a new user should be created,
        - user added as a member to the project's organization,
        - user added as a project contributor and,
        - an email being sent to them notfiying them they are now 
          a project contributor along with their permissions'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.list_create_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug
        })
        payload = {
            'email': batman_creds.email,
            'project': project1.id,
            'project_admin': False,
            'activity_viewer': False,
            'activity_editor': True
        }
        response = admin_client.post(url, payload, format='json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        data = response.data
        self.assertIn('user', data)
        self.assertIn('project', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        batman_user = UserModel.objects.get(email=batman_creds.email)
        self.assertEqual(batman_user.id, data['user'])
        self.assertEqual(payload['project'], data['project'])
        self.assertEqual(payload['project_admin'], data['project_admin'])
        self.assertEqual(payload['activity_viewer'], data['activity_viewer'])
        self.assertEqual(payload['activity_editor'], data['activity_editor'])

    def test_create_non_existant_user_contributor_by_project_admin_succeeds(self):
        '''Tests that a project admin (ProjectContributor.project_admin = True)
        can add a project contributor which does not match to an existing,
        user, to a project.
        - a new user should be created,
        - user added as a member to the project's organization,
        - user added as a project contributor and,
        - an email sent to them notfiying them they are now 
          a project contributor along with their permissions'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)

        url = reverse(self.list_create_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug
        })
        payload = {
            'email': batman_creds.email,
            'project': project1.id,
            'project_admin': False,
            'activity_viewer': False,
            'activity_editor': True
        }
        response = johndoe_client.post(url, payload, format='json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        data = response.data
        self.assertIn('user', data)
        self.assertIn('project', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        batman_user = UserModel.objects.get(email=batman_creds.email)
        self.assertEqual(batman_user.id, data['user'])
        self.assertEqual(payload['project'], data['project'])
        self.assertEqual(payload['project_admin'], data['project_admin'])
        self.assertEqual(payload['activity_viewer'], data['activity_viewer'])
        self.assertEqual(payload['activity_editor'], data['activity_editor'])

    def test_create_non_existant_user_contributor_by_non_project_user_non_admin_fails(self):
        '''Tests that a regular non-admin / non-project-admin cannot
        create project contributor'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)

        janedoe_client = APIClient()
        authenticate_jwt(janedoe_creds, janedoe_client)

        url = reverse(self.list_create_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug
        })
        payload = {
            'email': batman_creds.email,
            'project': project1.id,
            'project_admin': False,
            'activity_viewer': False,
            'activity_editor': True
        }
        response = janedoe_client.post(url, payload, format='json')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

        data = response.data
        self.assertNotIn('user', data)
        self.assertNotIn('project', data)
        self.assertNotIn('project_admin', data)
        self.assertNotIn('activity_viewer', data)
        self.assertNotIn('activity_editor', data)

    def test_create_existing_user_but_non_org_member_by_admin_succeeds(self):
        '''Tests that an existing user can be added as a project contributor
        by admin (User.is_staff = True)
        - user added as member to the project's organization
        - user added as a project contributor
        - email send to user notifying them they are now a project 
          contributor along with their permissions'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.list_create_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug
        })
        payload = {
            'email': self.janedoe_user.email,
            'project': project1.id,
            'project_admin': False,
            'activity_viewer': False,
            'activity_editor': True
        }
        response = admin_client.post(url, payload, format='json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        
        data = response.data
        self.assertIn('user', data)
        self.assertIn('project', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        self.assertEqual(self.janedoe_user.id, data['user'])
        self.assertEqual(payload['project'], data['project'])
        self.assertEqual(payload['project_admin'], data['project_admin'])
        self.assertEqual(payload['activity_viewer'], data['activity_viewer'])
        self.assertEqual(payload['activity_editor'], data['activity_editor'])

    def test_create_existing_user_but_non_org_member_by_project_admin_succeeds(self):
        '''Tests that an existing user can be added as a project contributor
        by project admin (ProjectContributor.project_admin = True)
        - user added as member to the project's organization
        - user added as a project contributor
        - email send to user notifying them they are now a project 
          contributor along with their permissions'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)

        url = reverse(self.list_create_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug
        })
        payload = {
            'email': self.janedoe_user.email,
            'project': project1.id,
            'project_admin': False,
            'activity_viewer': False,
            'activity_editor': True
        }
        response = johndoe_client.post(url, payload, format='json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        
        data = response.data
        self.assertIn('user', data)
        self.assertIn('project', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        self.assertEqual(self.janedoe_user.id, data['user'])
        self.assertEqual(payload['project'], data['project'])
        self.assertEqual(payload['project_admin'], data['project_admin'])
        self.assertEqual(payload['activity_viewer'], data['activity_viewer'])
        self.assertEqual(payload['activity_editor'], data['activity_editor'])
    
    def test_create_existing_user_but_non_org_member_by_non_admin_fails(self):
        '''Tests that a existing user cannot be added to as a Project Contributor
        by a regular non-admin user'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)

        janedoe_client = APIClient()
        authenticate_jwt(janedoe_creds, janedoe_client)

        url = reverse(self.list_create_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug
        })
        payload = {
            'email': self.janedoe_user.email,
            'project': project1.id,
            'project_admin': False,
            'activity_viewer': False,
            'activity_editor': True
        }
        response = janedoe_client.post(url, payload, format='json')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        
        data = response.data
        self.assertNotIn('user', data)
        self.assertNotIn('project', data)
        self.assertNotIn('project_admin', data)
        self.assertNotIn('activity_viewer', data)
        self.assertNotIn('activity_editor', data)

    def test_create_existing_user_and_org_member_by_admin_succeeds(self):
        '''Tests that an existing user who is a member or the Project's
        organization can be added as a project contributor by admin (User.is_staff = True)
        - user added as member to the project's organization
        - user added as a project contributor
        - email send to user notifying them they are now a project 
          contributor along with their permissions'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        org1.members.add(self.janedoe_user)

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.list_create_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug
        })
        payload = {
            'email': self.janedoe_user.email,
            'project': project1.id,
            'project_admin': False,
            'activity_viewer': False,
            'activity_editor': True
        }
        response = admin_client.post(url, payload, format='json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        
        data = response.data
        self.assertIn('user', data)
        self.assertIn('project', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        self.assertEqual(self.janedoe_user.id, data['user'])
        self.assertEqual(payload['project'], data['project'])
        self.assertEqual(payload['project_admin'], data['project_admin'])
        self.assertEqual(payload['activity_viewer'], data['activity_viewer'])
        self.assertEqual(payload['activity_editor'], data['activity_editor'])

    def test_create_existing_user_and_org_member_by_project_admin_succeeds(self):
        '''Tests that an existing user who is a member or the Project's
        organization can be added as a project contributor by project 
        admin (ProjectContributor.project_admin = True)
        - user added as member to the project's organization
        - user added as a project contributor
        - email send to user notifying them they are now a project 
          contributor along with their permissions'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        org1.members.add(self.janedoe_user)

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)

        url = reverse(self.list_create_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug
        })
        payload = {
            'email': self.janedoe_user.email,
            'project': project1.id,
            'project_admin': False,
            'activity_viewer': False,
            'activity_editor': True
        }
        response = johndoe_client.post(url, payload, format='json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        
        data = response.data
        self.assertIn('user', data)
        self.assertIn('project', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        self.assertEqual(self.janedoe_user.id, data['user'])
        self.assertEqual(payload['project'], data['project'])
        self.assertEqual(payload['project_admin'], data['project_admin'])
        self.assertEqual(payload['activity_viewer'], data['activity_viewer'])
        self.assertEqual(payload['activity_editor'], data['activity_editor'])
    
    def test_list_contributors_by_admin_succeeds(self):
        '''Tests that an admin (User.is_staff) can list all contributors to a project'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        ProjectContributor.objects.create(user=self.janedoe_user, project=project1, project_admin=True)

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.list_create_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug
        })
        response = admin_client.get(url, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        
        data = response.data
        self.assertIsInstance(data, list)
        self.assertEqual(2, len(data))

    def test_list_contributors_by_project_admin_succeeds(self):
        '''Tests that a project admin (ProjectContributor.project_admin = True)
        can list all contributors to a project'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        ProjectContributor.objects.create(user=self.janedoe_user, project=project1, project_admin=True)

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)

        url = reverse(self.list_create_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug
        })
        response = johndoe_client.get(url, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        
        data = response.data
        self.assertIsInstance(data, list)
        self.assertEqual(2, len(data))

    def test_list_contributors_by_non_project_admin_non_fails(self):
        '''Tests that a non-admin / non-project-admin cannot list project contributors'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        ProjectContributor.objects.create(user=self.janedoe_user, project=project1, project_admin=True)

        batman_user = batman_creds.create_user(is_active=True)
        batman_client = APIClient()
        authenticate_jwt(batman_creds, batman_client)

        url = reverse(self.list_create_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug
        })
        response = batman_client.get(url, format='json')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        
    def test_view_contributor_by_admin_succeeds(self):
        '''Tests that a admin (User.is_staff = True) can view contributor details'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        pc = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, project_admin=True)

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.detail_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug,
          'pk': pc.pk
        })
        response = admin_client.get(url, format='json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIn('project', data)
        self.assertIn('user', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        self.assertEqual(pc.user.id, data['user'])
        self.assertEqual(pc.project.id, data['project'])
        self.assertEqual(pc.project_admin, data['project_admin'])
        self.assertEqual(pc.activity_viewer, data['activity_viewer'])
        self.assertEqual(pc.activity_editor, data['activity_editor'])

    def test_view_contributor_by_project_admin_succeeds(self):
        '''Tests that a project admin (ProjectContributor.project_admin = True)
        can view contributor details'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        pc = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, project_admin=True)

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)

        url = reverse(self.detail_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug,
          'pk': pc.pk
        })
        response = johndoe_client.get(url, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIn('project', data)
        self.assertIn('user', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        self.assertEqual(pc.user.id, data['user'])
        self.assertEqual(pc.project.id, data['project'])
        self.assertEqual(pc.project_admin, data['project_admin'])
        self.assertEqual(pc.activity_viewer, data['activity_viewer'])
        self.assertEqual(pc.activity_editor, data['activity_editor'])

    def test_view_contributor_by_same_contributor_succeeds(self):
        '''Tests that a project contributor can view their own project
        contributor details'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        pc = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, project_admin=True)

        janedoe_client = APIClient()
        authenticate_jwt(janedoe_creds, janedoe_client)

        url = reverse(self.detail_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug,
          'pk': pc.pk
        })
        response = janedoe_client.get(url, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIn('project', data)
        self.assertIn('user', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        self.assertEqual(pc.user.id, data['user'])
        self.assertEqual(pc.project.id, data['project'])
        self.assertEqual(pc.project_admin, data['project_admin'])
        self.assertEqual(pc.activity_viewer, data['activity_viewer'])
        self.assertEqual(pc.activity_editor, data['activity_editor'])
    
    def test_view_contributor_by_non_admin_diff_user_fails(self):
        '''Tests that a project contributor's details are not viewable
        by non-admin / non-project-admin user who is different from the
        contributor being requested'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        pc = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, project_admin=True)

        batman_user = batman_creds.create_user(is_active=True)
        batman_client = APIClient()
        authenticate_jwt(batman_creds, batman_client)

        url = reverse(self.detail_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug,
          'pk': pc.pk
        })
        response = batman_client.get(url, format='json')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_update_contributor_existing_user_by_admin_succeeds(self):
        '''Tests that a admin (User.is_staff = True) can update contributor details'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        pc = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, project_admin=True)

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.detail_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug,
          'pk': pc.pk
        })
        batman_user = batman_creds.create_user(is_active=True)
        payload = {
          'email': batman_user.email,
          'project': project1.id,
          'project_admin': True,
          'activity_viewer': False,
          'activity_editor': False
        }
        response = admin_client.put(url, payload, format='json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIn('project', data)
        self.assertIn('user', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        self.assertEqual(batman_user.id, data['user'])
        self.assertEqual(payload['project'], data['project'])
        self.assertEqual(payload['project_admin'], data['project_admin'])
        self.assertEqual(payload['activity_viewer'], data['activity_viewer'])
        self.assertEqual(payload['activity_viewer'], data['activity_editor'])

    def test_update_contributor_existing_by_project_admin_succeeds(self):
        '''Tests that a project admin (ProjectContributor.project_admin = True)
        can update contributor details'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        pc = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, project_admin=True)

        janedoe_client = APIClient()
        authenticate_jwt(janedoe_creds, janedoe_client)

        url = reverse(self.detail_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug,
          'pk': pc.pk
        })
        batman_user = batman_creds.create_user(is_active=True)
        payload = {
          'email': batman_user.email,
          'project': project1.id,
          'project_admin': True,
          'activity_viewer': False,
          'activity_editor': False
        }
        response = janedoe_client.put(url, payload, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIn('project', data)
        self.assertIn('user', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        self.assertEqual(batman_user.id, data['user'])
        self.assertEqual(payload['project'], data['project'])
        self.assertEqual(payload['project_admin'], data['project_admin'])
        self.assertEqual(payload['activity_viewer'], data['activity_viewer'])
        self.assertEqual(payload['activity_viewer'], data['activity_editor'])


    def test_update_contributor_nonexisting_user_by_admin_succeeds(self):
        '''Tests that a admin (User.is_staff = True) can update contributor details'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        pc = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, project_admin=True)

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.detail_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug,
          'pk': pc.pk
        })
        payload = {
          'email': batman_creds.email,
          'project': project1.id,
          'project_admin': True,
          'activity_viewer': False,
          'activity_editor': False
        }
        response = admin_client.put(url, payload, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIn('project', data)
        self.assertIn('user', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        batman_user = UserModel.objects.get(email=batman_creds.email)
        self.assertEqual(batman_user.id, data['user'])
        self.assertEqual(payload['project'], data['project'])
        self.assertEqual(payload['project_admin'], data['project_admin'])
        self.assertEqual(payload['activity_viewer'], data['activity_viewer'])
        self.assertEqual(payload['activity_viewer'], data['activity_editor'])

    def test_update_contributor_nonexisting_by_project_admin_succeeds(self):
        '''Tests that a project admin (ProjectContributor.project_admin = True)
        can update contributor details'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        pc = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, project_admin=True)

        janedoe_client = APIClient()
        authenticate_jwt(janedoe_creds, janedoe_client)

        url = reverse(self.detail_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug,
          'pk': pc.pk
        })
        payload = {
          'email': batman_creds.email,
          'project': project1.id,
          'project_admin': True,
          'activity_viewer': False,
          'activity_editor': False

        }
        response = janedoe_client.put(url, payload, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIn('project', data)
        self.assertIn('user', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        batman_user = UserModel.objects.get(email=batman_creds.email)
        self.assertEqual(batman_user.id, data['user'])
        self.assertEqual(payload['project'], data['project'])
        self.assertEqual(payload['project_admin'], data['project_admin'])
        self.assertEqual(payload['activity_viewer'], data['activity_viewer'])
        self.assertEqual(payload['activity_viewer'], data['activity_editor'])

    def test_update_contributor_by_same_contributor_fails(self):
        '''Tests that a project contributor can not update their own project
        contributor details'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        pc = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_editor=True)

        janedoe_client = APIClient()
        authenticate_jwt(janedoe_creds, janedoe_client)

        url = reverse(self.detail_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug,
          'pk': pc.pk
        })
        payload = {
          'email': self.janedoe_user.email,
          'project': project1.id,
          'project_admin': True,
          'activity_viewer': False,
          'activity_editor': False
        }
        response = janedoe_client.put(url, payload, format='json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        data = response.data
        self.assertIn('project', data)
        self.assertIn('user', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        self.assertEqual(pc.user.id, data['user'])
        self.assertEqual(pc.project.id, data['project'])
        self.assertEqual(pc.project_admin, data['project_admin'])
        self.assertEqual(pc.activity_viewer, data['activity_viewer'])
        self.assertEqual(pc.activity_editor, data['activity_editor'])
    
    def test_update_contributor_by_non_admin_diff_user_fails(self):
        '''Tests that a project contributor's details are not updatable
        by non-admin / non-project-admin user who is different from the
        contributor being requested'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        pc = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_editor=True)

        batman_user = batman_creds.create_user(is_active=True)
        batman_client = APIClient()
        authenticate_jwt(batman_creds, batman_client)

        url = reverse(self.detail_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug,
          'pk': pc.pk
        })
        payload = {
          'email': self.janedoe_user.email,
          'project': project1.id,
          'project_admin': True,
          'activity_viewer': False,
          'activity_editor': False
        }
        response = janedoe_client.put(url, payload, format='json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        data = response.data
        self.assertIn('project', data)
        self.assertIn('user', data)
        self.assertIn('project_admin', data)
        self.assertIn('activity_viewer', data)
        self.assertIn('activity_editor', data)

        self.assertEqual(pc.user.id, data['user'])
        self.assertEqual(pc.project.id, data['project'])
        self.assertEqual(pc.project_admin, data['project_admin'])
        self.assertEqual(pc.activity_viewer, data['activity_viewer'])
        self.assertEqual(pc.activity_editor, data['activity_editor'])

    def test_delete_contributor_by_admin_succeeds(self):
        '''Tests that a admin (User.is_staff = True) can delete a contributor'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        pc = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, project_admin=True)

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.detail_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug,
          'pk': pc.pk
        })
        response = admin_client.delete(url, format='json')
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

        with self.assertRaises(ProjectContributor.DoesNotExist):
            ProjectContributor.objects.get(pk=pc.pk)


    def test_update_contributor_by_project_admin_succeeds(self):
        '''Tests that a project admin (ProjectContributor.project_admin = True)
        can delete a contributor'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        pc = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_editor=True)

        johndoe_client = APIClient()
        authenticate_jwt(johndoe_creds, johndoe_client)

        url = reverse(self.detail_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug,
          'pk': pc.pk
        })
        response = johndoe_client.delete(url, format='json')
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        
        with self.assertRaises(ProjectContributor.DoesNotExist):
            ProjectContributor.objects.get(pk=pc.pk)

    def test_update_contributor_by_same_contributor_fails(self):
        '''Tests that a project contributor can not delete their own project
        contributor instance'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        pc = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_editor=True)

        janedoe_client = APIClient()
        authenticate_jwt(janedoe_creds, janedoe_client)

        url = reverse(self.detail_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug,
          'pk': pc.pk
        })
        response = janedoe_client.delete(url, format='json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertIsNotNone(ProjectContributor.objects.get(pk=pc.pk))

    def test_update_contributor_by_non_admin_diff_user_fails(self):
        '''Tests that a project contributor is not deletable
        by non-admin / non-project-admin user who is different from the
        contributor being requested'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        pc = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_editor=True)

        batman_user = batman_creds.create_user(is_active=True)
        batman_client = APIClient()
        authenticate_jwt(batman_creds, batman_client)

        url = reverse(self.detail_view_name, kwargs={
          'org_slug': org1.slug,
          'project_slug': project1.slug,
          'pk': pc.pk
        })
        response = batman_client.delete(url, format='json')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertIsNotNone(ProjectContributor.objects.get(pk=pc.pk))
