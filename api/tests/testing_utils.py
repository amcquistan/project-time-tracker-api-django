
from django.shortcuts import reverse
from django.contrib.auth import get_user_model

from core.models import Organization, Project, ProjectContributor


class CredsHelper:
    def __init__(self, email, password):
        self.email = email
        self.password = password
    
    def to_dict(self):
        return {
          'email': self.email,
          'password': self.password
        }

    def create_user(self, **kwargs):
        return create_user(self.email, self.password, **kwargs)


admin_creds = CredsHelper('admin@mail.com', 'testpass123')
johndoe_creds = CredsHelper('johndoe@mail.com', 'password1')
janedoe_creds = CredsHelper('janedoe@mail.com', 'password2')
batman_creds = CredsHelper('batman@wayneenterprises.com', 'batmat123')
robin_creds = CredsHelper('robin@wayneenterprises.com', 'robin123')


def create_user(email, password, **kwargs):
    return get_user_model().objects.create_user(
        email=email,
        password=password,
        **kwargs
    )


def authenticate_jwt(creds, api_client, login_view_name='rest_login'):
    if isinstance(creds, CredsHelper):
        creds = creds.to_dict()

    url = reverse(login_view_name)
    response = api_client.post(url, creds, format='json')

    data = response.data
    if isinstance(data, dict) and 'access_token' in data:
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {data["access_token"]}')

    return response


def create_organization(name, contact):
    org = Organization.objects.create(name=name, contact=contact)
    org.members.add(contact)
    return org


def create_project(name, description, creator, organization):
    project = Project.objects.create(
        name=name,
        description=description,
        creator=creator,
        organization=organization
    )
    ProjectContributor.objects.create(
        user=organization.contact,
        project=project,
        project_admin=True
    )
    return project
