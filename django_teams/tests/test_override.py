from time import sleep
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from django_teams.models import override_manager, revert_manager

class OwnershipTests(TestCase):
    def test_overriding_queryset_no_errors(self):
        override_manager(User)
        User.objects.all()

        # If there are no errors, we should be good.. Revert
        revert_manager(User)
