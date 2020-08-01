from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils.timezone import now

from .utils import make_object_slug_field


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError('Email is required')
        
        user = self.model(email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password=password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=100, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class Organization(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(null=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    contact = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='organization_contacts')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL)

    def save(self, *args, **kwargs):
        if not self.slug:
            # self.slug = slugify(self.name)
            self.slug = make_object_slug_field(Organization, self.name)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    slug = models.SlugField(null=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_object_slug_field(Project, self.name)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class ProjectContributor(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    activity_viewer = models.BooleanField(default=False)
    activity_editor = models.BooleanField(default=False)
    project_admin = models.BooleanField(default=False)
    # rate = models.DecimalField(decimal_places=2, max_digits=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.project) + ' ' + str(self.user)


class ActivityEntry(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    slug = models.SlugField(null=False, unique=True)
    contributor = models.ForeignKey(ProjectContributor, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    minutes = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_object_slug_field(ActivityEntry, self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

