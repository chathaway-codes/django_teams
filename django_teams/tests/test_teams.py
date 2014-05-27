from time import sleep
from django.test import TestCase
from django.contrib.auth.models import User

from django_teams.models import Team

class TeamTests(TestCase):
    fixtures = ['test_data.json']
    def test_can_create_new_team(self):
        original_count = Team.objects.all().count()
        team = Team(name="Team Awesome")
        team.save()
        sleep(1)

        self.assertEqual(Team.objects.all().count(), original_count+1)

    def test_can_add_user_to_team(self):
        team = Team(name="Team Awesome")
        team.save()

        user = User.objects.get(pk=1)
        
        original_count = team.users.all().count()
        team.add_user(user)
        sleep(1)

        self.assertEqual(team.users.all().count(), original_count+1)
