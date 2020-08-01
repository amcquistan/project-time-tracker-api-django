from django.contrib.auth import get_user_model
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404

from rest_framework import serializers

from core.models import Organization, Project, ProjectContributor, ActivityEntry
from core.utils import send_activate_account_email


UserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ('email', 'name', 'password', 'phone_number', 'is_staff', 'is_superuser')
        read_only_fields = ('is_staff', 'is_superuser')
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 6}
        }

    def create(self, validated_data):
        return UserModel.objects.create_user(**validated_data)
      
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class OrganizationSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)
    class Meta:
        model = Organization
        fields = ('id', 'name', 'slug', 'created_at', 'updated_at', 'contact', 'members')
        read_only_fields = ('slug', 'created_at', 'updated_at', 'members')

    def create(self, validated_data):
        creator = get_object_or_404(get_user_model(), pk=validated_data['contact'].id)
        instance = super().create(validated_data)
        instance.members.add(creator)
        return instance


class ProjectsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'name', 'description', 'slug', 'created_at', 'updated_at', 'creator', 'organization')
        read_only_fields = ('slug', 'created_at', 'updated_at', 'creator')


def get_organization_for_project_serializer(view, slug_name='slug'):
    return get_object_or_404(Organization, slug=view.kwargs.get(slug_name))


def get_project_for_org_project_serializer(view, slug_name='slug'):
    org = get_organization_for_project_serializer(view, slug_name='org_slug')
    return get_object_or_404(Project, organization=org, slug=view.kwargs.get(slug_name))


class OrganizationProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'name', 'description', 'slug', 'created_at', 'updated_at', 'creator', 'organization')
        read_only_fields = ('slug', 'created_at', 'updated_at', 'organization')

    def get_organization(self):
        return get_organization_for_project_serializer(self.context['view'], slug_name='org_slug')

    def validate(self, data):
        organization = self.get_organization()
        if organization is None:
            raise serializers.ValidationError('Organization not found')
        return data

    def create(self, validated_data):
        instance = Project(**validated_data)
        instance.creator = self.context['request'].user
        organization = self.get_organization()
        instance.organization = organization
        instance.save()

        ProjectContributor.objects.create(
            user=instance.organization.contact,
            project=instance,
            project_admin=True
        )
        return instance


class ProjectContributorCreateUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    project = serializers.IntegerField()
    project_admin = serializers.BooleanField(default=False)
    activity_viewer = serializers.BooleanField(default=False)
    activity_editor = serializers.BooleanField(default=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        # fetch object early so if doesn't exist fails fast
        project = get_object_or_404(Project, pk=validated_data['project'])

        email = BaseUserManager.normalize_email(validated_data.get('email'))
        try:
            user = UserModel.objects.get(email=email)
        except ObjectDoesNotExist:
            user = UserModel.objects.create_user(email=email)

            request = self.context['request']
            send_activate_account_email(request, email)
        
        # django many-to-many fields will not add again,
        # if already exists it's essentially a noop
        project.organization.members.add(user)

        return ProjectContributor.objects.create(
            user=user,
            project=project,
            project_admin=validated_data['project_admin'],
            activity_viewer=validated_data['activity_viewer'],
            activity_editor=validated_data['activity_editor']
        )

    def update(self, instance, validated_data):
        project = get_object_or_404(Project, pk=validated_data['project'])

        email = BaseUserManager.normalize_email(validated_data.get('email'))
        try:
            user = UserModel.objects.get(email=email)
        except ObjectDoesNotExist:
            user = UserModel.objects.create_user(email=email)

            request = self.context['request']
            send_activate_account_email(request, email)
            project.organization.members.add(user)
        
        instance.user = user
        instance.project = project
        instance.project_admin = validated_data['project_admin']
        instance.activity_viewer = validated_data['activity_viewer']
        instance.activity_editor = validated_data['activity_editor']
        instance.save()
        return instance


class ProjectContributorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectContributor
        fields = ('id', 'project', 'user', 'project_admin', 'activity_viewer', 'activity_editor', 'created_at', 'updated_at')

    def get_organization(self):
        return get_organization_for_project_serializer(self.context['view'], slug_name='org_slug')

    def get_project(self):
        return get_project_for_org_project_serializer(self.context['view'], slug_name='project_slug')

    def validate(self, data):
        project = self.get_project()
        if project is None:
            raise serializers.ValidationError('Project not found')
        if project.id != data['project']:
            raise serializers.ValidationError('Project url slug does not match request body project id')
        return data


class ActivityEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityEntry
        fields = ('id', 'name', 'description', 'project', 'contributor', 'start', 'end', 'minutes')
