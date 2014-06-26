from time import sleep
import sys
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
        import django_teams.models
        django_teams.models.CurrentUser = None
        django_teams.models.CurrentTeam = None
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

    def test_default_team_hides_objects(self):
        import django_teams.models
        django_teams.models.CurrentUser = User.objects.get(pk=1)

        Team.objects.all().delete()
        Ownership.objects.all().delete()
        TeamStatus.objects.all().delete()

        team1 = Team(name="Team Mtn Dew")
        team1.save()
        team1.add_user(django_teams.models.CurrentUser, team_role=20)
        team2 = Team(name="Team ROFLCAT")
        team2.save()
        team2.add_user(django_teams.models.CurrentUser, team_role=20)

        site1 = Site.objects.get(pk=2)
        Ownership.grant_ownership(team1, site1)
        site2 = Site.objects.get(pk=3)
        Ownership.grant_ownership(team2, site2)

        django_teams.models.CurrentTeam = team2

        override_manager(Site)

        site_test = Site.objects.get(pk=3)
        self.assertEqual(site_test, site2)

        self.assertEqual(Site.objects.all().count(), 1)
        self.assertEqual(Site.objects.all()[0].id, 3)
        self.assertEqual(Site.objects.all()[0], site2)

        django_teams.models.CurrentUser = None
        django_teams.models.CurrentTeam = None
