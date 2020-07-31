from django.urls import path

from api.views import (
    OrganizationListCreateAPIView,
    OrganizationDetailAPIView,
    OrganizationMemberListCreateAPIView,
    OrganizationMemberDestroyAPIView,
    ProjectListAPIView,
    OrgProjectListCreateAPIView,
    OrgProjectDetailAPIView,
    ProjectContributorListCreateAPIView,
    ProjectContributorDetailAPIView,
    ActivityEntryListCreateAPIView,
    ActivityEntryDetailAPIVIew,
)

urlpatterns = [
    path('v1/organizations/',
         OrganizationListCreateAPIView.as_view(),
         name='organization-list-create'),

    path('v1/organizations/<slug:org_slug>/',
         OrganizationDetailAPIView.as_view(),
         name='organization-detail'),

    path('v1/organizations/<slug:org_slug>/members/',
         OrganizationMemberListCreateAPIView.as_view(),
         name='organization-member-list-create'),

    path('v1/organizations/<slug:org_slug>/members/<int:pk>/',
        OrganizationMemberDestroyAPIView.as_view(),
        name='organization-member-delete'),

    path('v1/projects/',
         ProjectListAPIView.as_view(),
         name='projects-list'),

    path('v1/organizations/<slug:org_slug>/projects/',
         OrgProjectListCreateAPIView.as_view(),
         name='organization-projects-list-create'),

    path('v1/organizations/<slug:org_slug>/projects/<slug:project_slug>/',
         OrgProjectDetailAPIView.as_view(),
         name='organization-projects-detail'),
  
    path('v1/organizations/<slug:org_slug>/projects/<slug:project_slug>/contributors/',
         ProjectContributorListCreateAPIView.as_view(),
         name='project-contributor-list-create'),

    path('v1/organizations/<slug:org_slug>/projects/<slug:project_slug>/contributors/<int:pk>/',
         ProjectContributorDetailAPIView.as_view(),
         name='project-contributor-detail'),
    
    path('v1/organizations/<slug:org_slug>/projects/<slug:project_slug>/activity-entries/',
         ActivityEntryListCreateAPIView.as_view(),
         name='activity-entry-list-create'),
    
    path('v1/organizations/<slug:org_slug>/projects/<slug:project_slug>/activity-entries/<slug:activity_slug>/',
         ActivityEntryDetailAPIVIew.as_view(),
         name='activity-entry-detail')
]
