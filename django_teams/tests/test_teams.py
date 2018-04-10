from time import sleep
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django_teams.models import Team, TeamStatus, Ownership


class TeamTests(TestCase):
    fixtures = ['test_data.json']

    def test_can_create_new_team(self):
        original_count = Team.objects.all().count()
        team = Team(name="Team Awesome")
        team.save()
        sleep(1)

        self.assertEqual(Team.objects.all().count(), original_count + 1)

    def test_can_add_user_to_team(self):
        team = Team(name="Team Awesome")
        team.save()

        user = User.objects.get(pk=1)

        original_count = team.users.all().count()
        team.add_user(user)
        sleep(1)

        self.assertEqual(team.users.all().count(), original_count + 1)

    def test_can_approve_user(self):
        team = Team(name="Team Awesome")
        team.save()

        user = User.objects.get(pk=1)

        original_count = team.users.all().count()
        team.add_user(user)
        sleep(1)

        self.assertEqual(team.users.all().count(), original_count + 1)

        ts = TeamStatus.objects.filter(user=user, team=team).reverse()[0]

        self.assertEqual(ts.role, 1)

        team.approve_user(user)

        ts = TeamStatus.objects.filter(user=user, team=team).reverse()[0]

        self.assertEqual(ts.role, 10)

    def test_cant_approve_user_with_no_invite(self):
        team = Team(name="Team Awesome")
        team.save()

        user = User.objects.get(pk=1)

        ts_count = TeamStatus.objects.filter(user=user, team=team).count()

        self.assertEqual(ts_count, 0)

        # Should throw error DNE
        try:
            team.approve_user(user)
        except ObjectDoesNotExist:
            pass

        ts_count = TeamStatus.objects.filter(user=user, team=team).count()

        self.assertEqual(ts_count, 0)

    def test_can_get_team_owners(self):
        team = Team(name="Team Awesome")
        team.save()
        user = User.objects.get(pk=1)

        team.add_user(user, team_role=20)
        owners = team.users.filter(teamstatus__role=20)
        self.assertIn(user, owners)

    def test_can_get_owned_objects(self):
        team = Team(name="Team Awesome")
        team.save()
        user = User.objects.get(pk=1)

        Ownership.grant_ownership(team, user)

        contenttype = ContentType.objects.get_for_model(User)
        owned_objects = []
        ownership_set = Ownership.objects.select_related('team',
                                                         'content_type').filter(team=team, content_type=contenttype)
        for ownership in ownership_set.iterator():
            owned_objects += [ownership.content_object]

        self.assertIn(user, owned_objects)

    def test_can_get_list_of_object_types(self):
        team = Team(name="Team Awesome")
        team.save()
        user = User.objects.get(pk=1)

        Ownership.grant_ownership(team, user)

        owned_object_types = []
        ownership_set = Ownership.objects.select_related('team').filter(team=team)
        for ownership in ownership_set.iterator():
            if ownership.content_type.model_class() not in owned_object_types:
                owned_object_types += [ownership.content_type.model_class()]

        self.assertIn(User, owned_object_types)
