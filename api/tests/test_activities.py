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

    def test_list_activity_entries_by_admin_for_project_succeeds(self):
        '''Tests that a admin (User.is_staff = True) can list activity 
        entries for a given project'''
        org1 = create_organization('Org 1', self.johndoe_user)
        project1 = create_project('Org 1 Project 1', 'abc', self.johndoe_user, org1)
        project2 = create_project('Org 1 Project 2', 'abc', self.johndoe_user, org1)

        ProjectContributor.objects.create(user=self.janedoe_user, project=project1, activity_editor=True)
        ProjectContributor.objects.create(user=self.batman_user, project=project1, activity_editor=True)

        ActivityEntry.objects.create(
            name='Test Contributors API',
            description='Write tests to test project contributors API',
            creator=self.janedoe_user,
            project=project1,
            minutes=180
        )
        ActivityEntry.objects.create(
            name='Test Activities API',
            description='Write tests to test activities API',
            creator=self.janedoe_user,
            project=project1,
            minutes=300
        )
        ActivityEntry.objects.create(
            name='Test Projects API',
            description='Write tests to test projects API',
            creator=self.batman_user,
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
        pass

    def test_list_activity_entries_by_project_contributor_activity_viewer_succeeds(self):
        '''Tests that all activity entries can be viewed by a project contributor for a project
        they have activity_view = True permission for'''
        pass

    def test_list_activity_entries_by_project_contributor_activity_editor_succeeds(self):
        '''Tests that a project contributor with activity_editor but, activity_viewer = False
        and project_admin = False can only view their activity entries for that project'''
        pass

    def test_list_activity_entries_by_non_project_contributor_fails(self):
        '''Tests that a project's activity entries cannot be viewed by a user
        who is not a project contributor'''
        pass

    def test_create_activity_entry_by_admin_succeeds(self):
        '''Tests that an activity entry can be entered for a project by a 
        admin (User.is_staff = True)'''
        pass

    def test_create_activity_entry_by_project_admin_succeeds(self):
        '''Tests that a project admin (ProjectContributor.project_admin = True)
        can create a activity entry for their project'''
        pass

    def test_create_activity_entry_by_activity_editor_succeeds(self):
        '''Tests that a project contributor with activity_editor = True
        can create a activity entry for the project'''
        pass

    def test_create_activity_entry_by_activity_viewer_fails(self):
        '''Tests that a activity entry cannot be created by a project
        contributor with activity_viewer = True'''
        pass

    def test_create_activity_entry_by_non_contributor_fails(self):
        '''Tests that a activity entry cannot be created by a non
        project contributor'''
        pass

    def test_view_activity_entry_by_admin_succeeds(self):
        '''Tests that an admin (User.is_staff = True) can view an
        activity entry'''
        pass

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
