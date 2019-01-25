from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class UserProfile(models.Model):
    """
    Extension of the default User model containing
    extra information necessary for UniAuth to run.
    """

    # User this profile is extending
    user = models.OneToOneField(get_user_model(), related_name='profile',
            on_delete=models.CASCADE, null=False)

    def __str__(self):
        try:
            return self.user.email or self.user.username
        except:
            return "NULL"


@receiver(post_save, sender=get_user_model())
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a Uniauth profile automatically when a User is created.

    If the User was given an email on creation, add it as a verified
    LinkedEmail immediately.
    """
    if created:
        profile = UserProfile.objects.create(user=instance)
        if profile and instance.email:
            LinkedEmail.objects.create(profile=profile,
                    address=instance.email, is_verified=True)


@receiver(post_save, sender=get_user_model())
def clear_old_tmp_users(sender, instance, created, **kwargs):
    """
    Deletes temporary users more than PASSWORD_RESET_TIMEOUT_DAYS
    old when a User is created.

    Does nothing if the user model does not have date_joined field.
    """
    if created:
        user_model = get_user_model()
        if hasattr(user_model, 'date_joined'):
            timeout_days = timedelta(days=settings.PASSWORD_RESET_TIMEOUT_DAYS)
            tmp_expire_date = (timezone.now() - timeout_days).replace(
                    hour=0, minute=0, second=0, microsecond=0)
            user_model.objects.filter(username__startswith='tmp-',
                    date_joined__lt=tmp_expire_date).delete()


class LinkedEmail(models.Model):
    """
    Represents an email address linked to a user's account.
    """

    # Person owning this email
    profile = models.ForeignKey('UserProfile', related_name='linked_emails',
            on_delete=models.CASCADE, null=False)

    # The email address
    address = models.EmailField(null=False)

    # Whether the linked email is verified
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        try:
            return "%s | %s" % (self.profile, self.address)
        except:
            return "NULL"


class Institution(models.Model):
    """
    Represents an organization holding a
    CAS server that can be logged into.
    """

    # Name of the institution
    name = models.CharField(max_length=30, null=False)

    # Slugified version of name
    slug = models.CharField(max_length=30, null=False, unique=True)

    # CAS server location
    cas_server_url = models.URLField(null=False)

    def __str__(self):
        try:
            return self.slug
        except:
            return "NULL"


class InstitutionAccount(models.Model):
    """
    Relates users to the accounts they have at
    institutions, and stores any associated data.
    """

    # The person the account is for
    profile = models.ForeignKey('UserProfile', related_name='accounts',
            on_delete=models.CASCADE, null=False)

    # The institution the account is with
    institution = models.ForeignKey('Institution', related_name='accounts',
            on_delete=models.CASCADE, null=False)

    # The ID used by the CAS server
    cas_id = models.CharField(max_length=30, null=False)

    def __str__(self):
        try:
            return "%s | %s | account" % (self.profile, self.institution)
        except:
            return "NULL"
