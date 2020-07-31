"""timetracker_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include

from dj_rest_auth.views import PasswordResetConfirmView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-admin/', include('rest_framework.urls')),

    # dj-rest-auth endpoints (see https://dj-rest-auth.readthedocs.io/en/latest/api_endpoints.html)
    # POST api/v1/auth/login/
    # POST api/v1/auth/logout/
    # POST api/v1/auth/password/reset/
    # POST api/v1/auth/password/reset/confirm/
    # POST api/v1/auth/password/change/
    # GET api/v1/auth/user/
    # PUT api/v1/auth/user/
    # PATCH api/v1/auth/user/
    path('api/v1/auth/', include('dj_rest_auth.urls')),

    # Needed because the email template will construct a url reset link like:
    #  - { protocol }}://{{ domain }}{% url 'password_reset_confirm' uidb64=uid token=token %}
    # as seen in base implementation in:
    #  - django/contrib/admin/templates/registration/password_reset_email.html
    # which needs to actually map back to a frontend SPA page which
    # will use the uidb64 and token route params and post the updated
    # password1 and password2 back up to the endpoint
    #  - POST api/v1/auth/password/reset/confirm/
    #      - uid
    #      - token
    #      - new_password1
    #      - new_password2
    path('password-reset/<uidb64>/<token>/', lambda request: HttpResponse(''), name='password_reset_confirm'),
    path('account-activation/<uidb64>/<token>/', lambda request: HttpResponse(''), name='account_activation'),

    path('api/', include('api.urls')),
]
