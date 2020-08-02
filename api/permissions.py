from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAdminUser

from core.models import Organization, Project, ProjectContributor


###############################################################################################
# Organization Project Permission
#
# Listing Projects 
# - Can be done by Admin (is_staff = True)
# - Can be done by user with ProjectContributor project_admin, activity_viewer,
#   activity_editor for the each project retrieved
# - 403 if not matching permissions, 401 if unauthenticated
#
# Creating Projects 
# - Can be done by Admin (is_staff = True)
# - Can be done by Organization contact
# - Should add Organization Contact as ProjectContributor with project_admin perm
# - 403 if not matching permissions, 401 if unauthenticated
#
# Viewing Project Detail
# - Can be done by Admin (is_staff = True)
# - Can be done by ProjectContributor with project_admin, activity_viewer, or activity_editor perm
# - 403 if not matching permissions, 401 if unauthenticated
#
# Updating Project Detail
# - Can be done by Admin (is_staff = True)
# - Can be done by ProjectContributor with project_admin perm
# - 403 if not matching permissions, 401 if unauthenticated
#
# Deleting Project
# - Can be done by Admin (is_staff = True)
# - 403 if not matching permissions, 401 if unauthenticated

class OrganizationProjectPermission(BasePermission):

    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
        
        org_slug = view.kwargs.get('org_slug')

        # if listing projects for org user must have
        # ProjectContributor project_admin, activity_viewer, or activity_editor
        # for at least one project associated with Organization
        if request.method == 'GET':
            return ProjectContributor.objects.filter(
                        user=request.user,
                        project__in=Project.objects.filter(organization__slug=org_slug)
                      ).filter(
                        Q(project_admin=True) | Q(activity_viewer=True) | Q(activity_editor=True)
                      ).count() > 0
          
        # if creating a project for org must must be org contact
        elif request.method not in SAFE_METHODS:
            org = Organization.objects.get(slug=org_slug)
            return org.contact == request.user
        
        return False
        
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if request.method == 'DELETE':
            return False

        try:
            contributor = ProjectContributor.objects.get(project=obj, user=request.user)
        except ProjectContributor.DoesNotExist:
            return False
        
        # user with ProjectContributor project_admin can do all but delete
        if contributor.project_admin:
            return True

        # if viewing user should be a ProjectContributor with project_admin
        if request.method in SAFE_METHODS and (contributor.activity_editor or contributor.activity_viewer):
            return True
        
        return False


class OrganizationMemberPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True

        org = Organization.objects.get(slug=view.kwargs.get('org_slug'))
        return org.members.filter(id=request.user.id).count() > 0

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        org = Organization.objects.get(slug=view.kwargs.get('org_slug'))
        return org.contact == request.user


class ProjectListPermission(BasePermission):
    def has_permission(self, request, view):
        return True
    
    def has_object_permission(self, request, view, obj):
        return True


#################################################################################
# Organization Permission
#
# Creating Organization
# - Can only be done by Admin (is_staff)
# - return 403 if not admin or 401 if unauthenticated
#
# Listing Organization
# - Can be done by Admin (is_staff = True)
# - Can be done by users who are members of an Organization
# - returns empty list if conditions not met and relies on get_queryset()
#   method of view, 401 if unauthenticated
#
# View Organization Details
# - Can be done by admin (is_staff = True)
# - Can be done by users who are members of an Organization
# - returns 403 if conditions are not met and relies, 401 if unauthenticated
# 
class OrganizationPermission(BasePermission):

    def has_permission(self, request, view):
        if request.user.is_staff:
            return True

        if 'org_slug' in view.kwargs:
            try:
                Organization.objects.get(slug=view.kwargs.get('org_slug'), contact=request.user)
            except ObjectDoesNotExist:
                return False
        return Organization.objects.filter(contact=request.user).count() > 0

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        # only admin (is_staff = True) can delete
        if request.method == 'DELETE':
            return False

        if hasattr(obj, 'contact'):
            # dealing with Organization object
            return obj.contact == request.user
        
        if hasattr(obj, 'organization'):
            # dealing with Project object
            return obj.organization.contact == request.user
        
        return False


#################################################################################
# Project Contributor Permission
#
# Creating Project Contributor
# - Can be done by Admin (is_staff)
# - Can be done by Project Admin (ProjectContributor.project_admin)
# - return 403 if not admin or 401 if unauthenticated
#
# Listing Project Contributor
# - Can be done by Admin (is_staff = True)
# - Can be done by Project Admin (ProjectContributor.project_admin)
# - returns empty list if conditions not met and relies on get_queryset()
#   method of view, 401 if unauthenticated
#
# View / Updating / Deleting Project Contributor
# - Can be done by admin (is_staff = True)
# - Can only be done by Project Admin (ProjectContributor.project_admin)
# - returns 403 if conditions are not met and relies, 401 if unauthenticated
# 
class ProjectContributorPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True

        project_contributor = get_object_or_404(ProjectContributor,
            user=request.user,
            project__slug=view.kwargs['project_slug']
        )

        return project_contributor.project_admin

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        user_project_contributor = get_object_or_404(ProjectContributor,
            user=request.user,
            project__slug=view.kwargs['project_slug']
        )
        if request.method in SAFE_METHODS and user_project_contributor.user == request.user:
            return True
        
        return user_project_contributor.project_admin


#################################################################################
# Activity Entry Permission
#
# Creating Activity Entry for a Project
# - Can be done by Project Contributor with activity_editor permissions for a project
#   they have activity_editor permission with
# - return 404 if not admin or project contributor with activity_editor permission
#   or 401 if unauthenticated
#
# Listing Activity Entries for a Project
# - Can be done by Admin (is_staff = True) for any Project
# - Can be done by Project Admin (ProjectContributor.project_admin) for the project
#   which they are a project admin for
# - Can be done by a Project Contributor for which they are activity_viewers for
# - Can be done by a Project Contributor for which they are a activity_editor for
#   but, they will only be able to list their own project activities
# - returns empty list if conditions not met and relies on get_queryset()
#   method of view, 401 if unauthenticated
#
# View Activity Entries for a Project
# - Can be done by admin (is_staff = True) for any activity entry
# - Can be done by a Project Admin (ProjectContributor.project_admin) for the project
#   they are an admin for
# - Can be done by Project Contributor for which they are activity_viewer 
#   or activity_editor for
# - returns 403 if conditions are not met, 401 if unauthenticated
# 
# Update / Delete Activity Entry for Project
# - Can be done by admin (User.is_staff = True) for any activity entry
# - Can be done by Project Admin (ProjectContributor.project_admin) for the project
#   which they are a project admin for
# - Can be done by Project Contributor for which they are activity_editor for
# - returns 403 if conditions are not met, 401 if unauthenticated
class ActivityEntryPermission(BasePermission):
    def get_project_contributor(self, user, project_slug):
        return get_object_or_404(ProjectContributor,
                                 user=user,
                                 project__slug=project_slug)
        
    def has_permission(self, request, view):
        if request.method == 'POST' and request.user.is_staff:
            return False
        
        if request.user.is_staff:
            return True

        contributor = self.get_project_contributor(request.user,
                                                  view.kwargs['project_slug'])

        if request.method == 'POST':
            # project admins can create a activity entry
            if contributor.project_admin:
                return False

            # contributor's with editor perm can make their own activity entries
            if contributor.activity_editor and request.data['contributor'] == contributor.id:
                return True

            return False

        return contributor.project_admin or contributor.activity_viewer \
                  or contributor.activity_editor

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        contributor = self.get_project_contributor(request.user,
                                                  view.kwargs['project_slug'])

        if obj.contributor == contributor or contributor.project_admin:
            return True

        if request.method == 'GET' and contributor.activity_viewer:
            return True

        return False
