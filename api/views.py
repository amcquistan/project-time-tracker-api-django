from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAdminUser

from core.models import (
    Organization,
    Project,
    ProjectContributor,
    ActivityEntry
)

from .permissions import (
    OrganizationPermission,
    ProjectListPermission,
    OrganizationMemberPermission,
    OrganizationProjectPermission,
    ProjectContributorPermission,
    ActivityEntryPermission,
)
from .serializers import (
    UserSerializer,
    OrganizationSerializer,
    ProjectsListSerializer,
    OrganizationProjectSerializer,
    ProjectContributorSerializer,
    ProjectContributorCreateUpdateSerializer,
    ActivityEntrySerializer,
)


class OrganizationListCreateAPIView(ListCreateAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticated, OrganizationPermission,)

    def get_queryset(self):
        qs = Organization.objects.all()
        if self.request.user.is_staff:
            return qs
        
        return qs.filter(contact=self.request.user)


class OrganizationDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticated, OrganizationPermission,)

    def get_object(self):
        org_slug = self.kwargs.get('org_slug')
        obj = get_object_or_404(Organization, slug=org_slug)
        self.check_object_permissions(self.request, obj)
        return obj


class OrganizationMemberDestroyAPIView(DestroyAPIView):
    permission_classes = (IsAuthenticated, OrganizationMemberPermission,)

    def get_object(self):
        org = get_object_or_404(Organization, slug=self.kwargs['org_slug'])
        try:
            member = org.members.get(pk=self.kwargs['pk'])
        except ObjectDoesNotExist:
            raise Http404('Entity not found')

        self.check_object_permissions(self.request, member)
        return member

    def delete(self, request, *args, **kwargs):
        member = self.get_object()
        org = get_object_or_404(Organization, slug=self.kwargs['org_slug'])
        org.members.remove(member)

        ProjectContributor.objects.filter(user=member,
            project__organization=org).delete()
 
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationMemberListCreateAPIView(ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, OrganizationMemberPermission,)

    def get_queryset(self):
        organization = get_object_or_404(Organization, slug=self.kwargs['org_slug'])
        return organization.members.all()

    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        org = get_object_or_404(Organization, slug=self.kwargs['org_slug'])
        org.members.add(get_object_or_404(get_user_model(), pk=user_id))
        serializer = OrganizationSerializer(org)
        data = serializer.data
        return Response(data=data, status=status.HTTP_201_CREATED)


class ProjectListAPIView(ListAPIView):
    serializer_class = ProjectsListSerializer
    permission_classes = (IsAuthenticated, ProjectListPermission, )

    def get_queryset(self):
        if self.request.user.is_staff:
            return Project.objects.all()

        qs = (ProjectContributor.objects
                .select_related('project')
                .filter(user=self.request.user)
                .filter(Q(project_admin=True) | Q(activity_viewer=True) | Q(activity_editor=True))
                .all())
        projects = [q.project for q in qs]
        return projects


class OrgProjectListCreateAPIView(ListCreateAPIView):
    serializer_class = OrganizationProjectSerializer
    permission_classes = (IsAuthenticated, OrganizationProjectPermission,)

    def get_queryset(self):
        org_slug = self.kwargs['org_slug']
        if self.request.user.is_staff:
            return Project.objects.filter(organization__slug=org_slug).all()

        qs = (ProjectContributor.objects
                    .filter(user=self.request.user)
                    .filter(Q(project_admin=True) | Q(activity_viewer=True) | Q(activity_editor=True))
                    .select_related('project').all())
        return [q.project for q in qs]


class OrgProjectDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrganizationProjectSerializer
    permission_classes = (IsAuthenticated, OrganizationProjectPermission,)
    
    def get_object(self):
        project = get_object_or_404(Project,
            organization__slug=self.kwargs['org_slug'],
            slug=self.kwargs['project_slug'])

        self.check_object_permissions(self.request, project)
        return project


class ProjectContributorListCreateAPIView(ListCreateAPIView):
    serializer_class = ProjectContributorSerializer
    permission_classes = (IsAuthenticated, ProjectContributorPermission,)

    def get_queryset(self):
        project = get_object_or_404(Project, organization__slug=self.kwargs['org_slug'], slug=self.kwargs['project_slug'])
        return ProjectContributor.objects.filter(project=project).all()

    def post(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        creation_serializer = ProjectContributorCreateUpdateSerializer(data=request.data, context=context)
        if creation_serializer.is_valid():
            project_contributor = creation_serializer.save()
            serializer = self.serializer_class(instance=project_contributor)
            return Response(data=serializer.data,
                            status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectContributorDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectContributorSerializer
    permission_classes = (IsAuthenticated, ProjectContributorPermission,)

    def get_object(self):
        project = get_object_or_404(Project,
                                    slug=self.kwargs['project_slug'],
                                    organization__slug=self.kwargs['org_slug'])
        obj = get_object_or_404(ProjectContributor,
                                project=project,
                                pk=self.kwargs['pk'])
        self.check_object_permissions(self.request, obj)
        return obj

    def put(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        update_serializer = ProjectContributorCreateUpdateSerializer(
            instance=self.get_object(),
            data=request.data,
            context=context
        )
        if update_serializer.is_valid():
            updated_obj = update_serializer.save()
            serializer = self.serializer_class(instance=updated_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(data=update_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivityEntryListCreateAPIView(ListCreateAPIView):
    serializer_class = ActivityEntrySerializer
    permission_classes = (IsAuthenticated, ActivityEntryPermission, )

    def get_queryset(self):
        project_slug = self.kwargs['project_slug']
        qs = ActivityEntry.objects.all()
        if self.request.user.is_staff:
            return qs.filter(project__slug=project_slug)
        
        contributor = get_object_or_404(ProjectContributor,
                                        project__slug=project_slug,
                                        user=self.request.user)
        if contributor.project_admin or contributor.activity_viewer:
            return qs.filter(project=contributor.project)
        
        return qs.filter(project=contributor.project, contributor=contributor)


class ActivityEntryDetailAPIVIew(RetrieveUpdateDestroyAPIView):
    serializer_class = ActivityEntrySerializer
    permission_classes = (IsAuthenticated, ActivityEntryPermission, )

    def get_object(self):
        obj = get_object_or_404(ActivityEntry,
                                project__slug=self.kwargs['project_slug'],
                                slug=self.kwargs['activity_slug'])
        self.check_object_permissions(self.request, obj)
        return obj
