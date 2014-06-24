from time import sleep
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from django_teams.models import override_manager, revert_manager, Team, TeamStatus, Ownership
from django.contrib.sites.models import Site

class OwnershipTests(TestCase):
    fixtures = ['test_data.json']

    def tearDown(self):
        revert_manager(Site)

    def test_overriding_queryset_no_errors(self):
        override_manager(User)
        User.objects.all()

        # If there are no errors, we should be good.. Revert
        revert_manager(User)

    def test_can_override_sites(self):
        """
        Attempts to override the sites framework so that we can only query sites we own
        - This is only a proof-of-concept test, as I don't want to include another app for testing
        """
        # Set the current User
        import django_teams.models
        django_teams.models.CurrentUser = User.objects.get(pk=1)

        self.assertEqual(Site.objects.all().count(), 3)
        override_manager(Site)

        self.assertEqual(Site.objects.all().count(), 0)

    def test_can_gain_access(self):
        import django_teams.models
        django_teams.models.CurrentUser = User.objects.get(pk=1)

        self.assertEqual(Site.objects.all().count(), 3)
        site = Site.objects.get(pk=1)
        override_manager(Site)

        # Try granting the user access to one site
        team = Team(name="Team awesome")
        team.save()

        team.add_user(django_teams.models.CurrentUser, team_role=20)

        Ownership.grant_ownership(team, site)

        self.assertEqual(Site.objects.all().count(), 1)
