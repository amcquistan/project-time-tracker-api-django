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
    robin_creds,
    create_organization,
    create_project,
)
from core.models import (
    Organization,
    Project,
    ProjectContributor,
    ActivityEntry
)


class ActivityEntryTests(TestCase):
    create_list_view_name = 'activity-entry-list-create'
    detail_view_name = 'activity-entry-detail'

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = admin_creds.create_user(
          is_active=True,
          is_staff=True
        )
        cls.johndoe_user = johndoe_creds.create_user(is_active=True)
        cls.janedoe_user = janedoe_creds.create_user(is_active=True)
        cls.batman_user = batman_creds.create_user(is_active=True)

    def test_list_activity_entries_by_admin_succeeds(self):
        '''Tests that a admin (User.is_staff = True) can list activity 
        entries for a given project'''
        robin_user = robin_creds.create_user(is_active=True)
        org1 = create_organization('Org 1', robin_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        janedoe_contrib = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_editor=True)
        batman_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project1, activity_editor=True)

        ActivityEntry.objects.create(
            name='Test Contributors API',
            description='Write tests to test project contributors API',
            contributor=janedoe_contrib,
            project=project1,
            minutes=180
        )
        ActivityEntry.objects.create(
            name='Test Activities API',
            description='Write tests to test activities API',
            contributor=janedoe_contrib,
            project=project1,
            minutes=300
        )
        ActivityEntry.objects.create(
            name='Test Projects API',
            description='Write tests to test projects API',
            contributor=batman_contrib,
            project=project1,
            minutes=300
        )

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.create_list_view_name, kwargs={
            'org_slug': org1.slug,
            'project_slug': project1.slug
        })
        response = admin_client.get(url, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertEqual(3, len(response.data))

    def test_list_activity_entries_by_project_admin_succeeds(self):
        '''Tests that a project admin (ProjectContributor.project_admin = True)
        can list the activity entries for a project they are an admin for'''
        robin_user = robin_creds.create_user(is_active=True)
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        robin_contrib = ProjectContributor.objects.create(user=robin_user, project=project1, project_admin=True)
        janedoe_contrib = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_editor=True)
        batman_proj1_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project1, activity_editor=True)
        batman_proj2_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project2, activity_editor=True)

        ActivityEntry.objects.create(
            name='Test Contributors API',
            description='Write tests to test project contributors API',
            contributor=janedoe_contrib,
            project=project1,
            minutes=180
        )
        ActivityEntry.objects.create(
            name='Test Activities API',
            description='Write tests to test activities API',
            contributor=janedoe_contrib,
            project=project1,
            minutes=300
        )
        ActivityEntry.objects.create(
            name='Test Projects API',
            description='Write tests to test projects API',
            contributor=batman_proj1_contrib,
            project=project1,
            minutes=300
        )
        ActivityEntry.objects.create(
            name='Test Projects API',
            description='Write tests to test projects API',
            contributor=batman_proj2_contrib,
            project=project2,
            minutes=300
        )

        robin_client = APIClient()
        authenticate_jwt(robin_creds, robin_client)

        url = reverse(self.create_list_view_name, kwargs={
            'org_slug': org1.slug,
            'project_slug': project1.slug
        })
        response = robin_client.get(url, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertEqual(3, len(response.data))

    def test_list_activity_entries_by_project_contributor_activity_viewer_succeeds(self):
        '''Tests that all activity entries can be viewed by a project contributor for a project
        they have activity_view = True permission for'''
        robin_user = robin_creds.create_user(is_active=True)
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        robin_contrib = ProjectContributor.objects.create(user=robin_user, project=project1, activity_viewer=True)
        janedoe_contrib = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_editor=True)
        batman_proj1_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project1, activity_editor=True)
        batman_proj2_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project2, activity_editor=True)

        ActivityEntry.objects.create(
            name='Test Contributors API',
            description='Write tests to test project contributors API',
            contributor=janedoe_contrib,
            project=project1,
            minutes=180
        )
        ActivityEntry.objects.create(
            name='Test Activities API',
            description='Write tests to test activities API',
            contributor=janedoe_contrib,
            project=project1,
            minutes=300
        )
        ActivityEntry.objects.create(
            name='Test Projects API',
            description='Write tests to test projects API',
            contributor=batman_proj1_contrib,
            project=project1,
            minutes=300
        )
        ActivityEntry.objects.create(
            name='Test Projects API',
            description='Write tests to test projects API',
            contributor=batman_proj2_contrib,
            project=project2,
            minutes=300
        )

        robin_client = APIClient()
        authenticate_jwt(robin_creds, robin_client)

        url = reverse(self.create_list_view_name, kwargs={
            'org_slug': org1.slug,
            'project_slug': project1.slug
        })
        response = robin_client.get(url, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertEqual(3, len(response.data))

    def test_list_activity_entries_by_project_contributor_activity_editor_succeeds(self):
        '''Tests that a project contributor with activity_editor but, activity_viewer = False
        and project_admin = False can only view their activity entries for that project'''
        robin_user = robin_creds.create_user(is_active=True)
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        robin_contrib = ProjectContributor.objects.create(user=robin_user, project=project1, activity_viewer=True)
        janedoe_contrib = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_editor=True)
        batman_proj1_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project1, activity_editor=True)
        batman_proj2_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project2, activity_editor=True)

        ActivityEntry.objects.create(
            name='Test Contributors API',
            description='Write tests to test project contributors API',
            contributor=janedoe_contrib,
            project=project1,
            minutes=180
        )
        ActivityEntry.objects.create(
            name='Test Activities API',
            description='Write tests to test activities API',
            contributor=janedoe_contrib,
            project=project1,
            minutes=300
        )
        ActivityEntry.objects.create(
            name='Test Projects API',
            description='Write tests to test projects API',
            contributor=batman_proj1_contrib,
            project=project1,
            minutes=300
        )
        ActivityEntry.objects.create(
            name='Test Projects API',
            description='Write tests to test projects API',
            contributor=batman_proj2_contrib,
            project=project2,
            minutes=300
        )

        batman_client = APIClient()
        authenticate_jwt(batman_creds, batman_client)

        url = reverse(self.create_list_view_name, kwargs={
            'org_slug': org1.slug,
            'project_slug': project1.slug
        })
        response = batman_client.get(url, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertEqual(1, len(response.data))

    def test_list_activity_entries_by_non_project_contributor_fails(self):
        '''Tests that a project's activity entries cannot be viewed by a user
        who is not a project contributor'''
        robin_user = robin_creds.create_user(is_active=True)
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        janedoe_contrib = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_editor=True)
        batman_proj1_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project1, activity_editor=True)
        batman_proj2_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project2, activity_editor=True)

        ActivityEntry.objects.create(
            name='Test Contributors API',
            description='Write tests to test project contributors API',
            contributor=janedoe_contrib,
            project=project1,
            minutes=180
        )
        ActivityEntry.objects.create(
            name='Test Activities API',
            description='Write tests to test activities API',
            contributor=janedoe_contrib,
            project=project1,
            minutes=300
        )
        ActivityEntry.objects.create(
            name='Test Projects API',
            description='Write tests to test projects API',
            contributor=batman_proj1_contrib,
            project=project1,
            minutes=300
        )
        ActivityEntry.objects.create(
            name='Test Projects API',
            description='Write tests to test projects API',
            contributor=batman_proj2_contrib,
            project=project2,
            minutes=300
        )

        robin_client = APIClient()
        authenticate_jwt(robin_creds, robin_client)

        url = reverse(self.create_list_view_name, kwargs={
            'org_slug': org1.slug,
            'project_slug': project1.slug
        })
        response = robin_client.get(url, format='json')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_create_activity_entry_by_activity_editor_succeeds(self):
        '''Tests that a project contributor with activity_editor = True
        can create a activity entry for the project'''
        robin_user = robin_creds.create_user(is_active=True)
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        johndoe_contrib = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_viewer=True)
        batman_proj1_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project1, activity_editor=True)
        batman_proj2_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project2, activity_editor=True)


        batman_client = APIClient()
        authenticate_jwt(batman_creds, batman_client)

        url = reverse(self.create_list_view_name, kwargs={
            'org_slug': org1.slug,
            'project_slug': project1.slug
        })
        payload = {
            'name': 'An Activity',
            'description': 'Activity description',
            'contributor': batman_proj1_contrib.id,
            'project': project1.id,
            'minutes': 60
        }
        response = batman_client.post(url, payload, format='json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        data = response.data
        self.assertIn('name', data)
        self.assertIn('description', data)
        self.assertIn('contributor', data)
        self.assertIn('project', data)
        self.assertIn('start', data)
        self.assertIn('end', data)
        self.assertIn('minutes', data)

        self.assertEquals(payload['name'], data['name'])
        self.assertEquals(payload['description'], data['description'])
        self.assertEquals(payload['contributor'], data['contributor'])
        self.assertEquals(payload['project'], data['project'])
        self.assertIsNone(data['start'])
        self.assertIsNone(data['end'])
        self.assertEquals(payload['minutes'], data['minutes'])

    def test_create_activity_entry_by_activity_viewer_fails(self):
        '''Tests that a activity entry cannot be created by a project
        contributor with activity_viewer = True'''
        robin_user = robin_creds.create_user(is_active=True)
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        johndoe_contrib = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_viewer=True)
        batman_proj1_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project1, activity_viewer=True)
        batman_proj2_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project2, activity_editor=True)

        batman_client = APIClient()
        authenticate_jwt(batman_creds, batman_client)

        url = reverse(self.create_list_view_name, kwargs={
            'org_slug': org1.slug,
            'project_slug': project1.slug
        })
        payload = {
            'name': 'An Activity',
            'description': 'Activity description',
            'contributor': batman_proj1_contrib.id,
            'project': project1.id,
            'minutes': 60
        }
        response = batman_client.post(url, payload, format='json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        data = response.data
        self.assertNotIn('name', data)
        self.assertNotIn('description', data)
        self.assertNotIn('contributor', data)
        self.assertNotIn('project', data)
        self.assertNotIn('start', data)
        self.assertNotIn('end', data)
        self.assertNotIn('minutes', data)

    def test_create_activity_entry_by_non_contributor_fails(self):
        '''Tests that a activity entry cannot be created by a non
        project contributor'''
        robin_user = robin_creds.create_user(is_active=True)
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_viewer=True)
        ProjectContributor.objects.create(user=self.batman_user, project=project1, activity_editor=True)
        ProjectContributor.objects.create(user=self.batman_user, project=project2, activity_editor=True)

        robin_client = APIClient()
        authenticate_jwt(robin_creds, robin_client)

        url = reverse(self.create_list_view_name, kwargs={
            'org_slug': org1.slug,
            'project_slug': project1.slug
        })
        payload = {
            'name': 'An Activity',
            'description': 'Activity description',
            'project': project1.id,
            'minutes': 60
        }
        response = robin_client.post(url, payload, format='json')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

        data = response.data
        self.assertNotIn('name', data)
        self.assertNotIn('description', data)
        self.assertNotIn('contributor', data)
        self.assertNotIn('project', data)
        self.assertNotIn('start', data)
        self.assertNotIn('end', data)
        self.assertNotIn('minutes', data)

    def test_view_activity_entry_by_admin_succeeds(self):
        '''Tests that an admin (User.is_staff = True) can view an
        activity entry'''
        robin_user = robin_creds.create_user(is_active=True)
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        janedoe_contrib = ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_viewer=True)
        batman_proj1_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project1, activity_viewer=True)
        batman_proj2_contrib = ProjectContributor.objects.create(user=self.batman_user, project=project2, activity_editor=True)

        ae = ActivityEntry.objects.create(
            name='An Activity',
            description='A new activity entry',
            contributor=janedoe_contrib,
            project=project1,
            minutes=60
        )

        admin_client = APIClient()
        authenticate_jwt(admin_creds, admin_client)

        url = reverse(self.detail_view_name, kwargs={
            'org_slug': org1.slug,
            'project_slug': project1.slug,
            'activity_slug': ae.slug
        })
        response = admin_client.get(url, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertIn('name', data)
        self.assertIn('description', data)
        self.assertIn('contributor', data)
        self.assertIn('project', data)
        self.assertIn('start', data)
        self.assertIn('end', data)
        self.assertIn('minutes', data)

    def test_view_activity_entry_by_project_admin_succeeds(self):
        '''Tests that a project admin (ProjectContributor.project_admin = True)
        can view an activity entry'''
        pass

    def test_view_activity_entry_by_activity_viewer_succeeds(self):
        '''Tests that an activity entry can be viewed by a user
        who is a project's contributor with activity_viewer permission'''
        pass

    def test_view_activity_entry_by_activity_editor_succeeds(self):
        '''Tests that an activity entry can be viewed by the user
        with project contributor activity_editor for that activity entry'''
        pass

    def test_view_activity_entry_by_non_contributor_fails(self):
        '''Tests that a activity entry cannot be viewed by a user
        who is not a project contributor for that entry's project'''
        pass

    def test_update_activity_entry_by_admin_succeeds(self):
        '''Tests that a activity entry can be updated by an
        admin (User.is_staff = True)'''
        pass

    def test_update_activity_entry_by_project_admin_succeeds(self):
        '''Tests that a activity entry can be updated by a user who is
        a project admin for the project associated with the activity entry'''
        pass

    def test_update_activity_entry_by_activity_editor_succeeds(self):
        '''Tests that a activity entry can be updated by a user who is 
        a activity_editor for that activity entry'''
        pass

    def test_update_activity_entry_by_non_contributor_fails(self):
        '''Tests that a activity entry cannot be updated by a user who is
        not a project contributor'''
        pass

    def test_delete_activity_entry_by_admin_succeeds(self):
        '''Tests that a admin can delete an activity entry'''
        pass

    def test_delete_activity_entry_by_project_admin_succeeds(self):
        '''Tests that a project admin can delete an activity associated with
        the project they are an admin for'''
        pass

    def test_delete_activity_entry_by_activity_editor_succeeds(self):
        '''Tests that a activity entry can be deleted by a project
        contributor who is an activity editor for that activity entry'''
        pass

    def test_delete_activity_entry_by_activity_viewer_fails(self):
        '''Tests that a activity entry cannot be deleted by a project
        contributor who is an activity viewer for that activity'''
        pass

    def test_delete_activity_entry_by_non_contributor_fails(self):
        '''Tests that a activity entry cannot be deleted by a 
        non-project-contributor'''
        pass
