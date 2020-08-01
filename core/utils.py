from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.shortcuts import get_current_site
from django.template import loader
from django.template.defaultfilters import slugify
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def send_activate_account_email(request, email,
                                token_generator=default_token_generator,
                                email_text_template='accounts/activate_account_email.txt',
                                email_html_template='accounts/activate_account_email.html'):
    current_site = get_current_site(request)
    site_name = current_site.name
    domain = current_site.domain
    user = get_user_model().objects.get(email=email)

    context = {
      'email': email,
      'domain': domain,
      'site_name': site_name,
      'uid': urlsafe_base64_encode(force_bytes(user.pk)),
      'user': user,
      'token': token_generator.make_token(user),
      'protocol': 'https'
    }
    
    subject = '{} Account Confirmation'.format(site_name)
    body = loader.render_to_string(email_text_template, context)

    email_message = EmailMultiAlternatives(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )
    html_email = loader.render_to_string(email_html_template, context)
    email_message.attach_alternative(html_email, 'text/html')
    email_message.send()


def make_object_slug_field(klass, slug_input):
    slug = slugify(slug_input)
    for i in range(2, 10000):
        try:
            _ = klass.objects.get(slug=slug)
            slug = '{}-{}'.format(slugify(slug_input), i)
        except klass.DoesNotExist:
            break
    return slug
