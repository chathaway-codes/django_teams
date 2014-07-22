import sys
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.test.client import Client
 
from django_teams.models import Team, TeamStatus

class ListTeamsTests(TestCase):
    fixtures = ['test_data.json']

    def test_can_get_route(self):
        self.assertTrue(reverse('team-list') != None)

    def test_can_load_page(self):
        response = self.client.get(reverse('team-list'))

        self.assertEqual(response.status_code, 200)

    def test_page_contains_all_teams(self):
        Team(name="Team Awesome").save()
        Team(name="Team Silly").save()
        Team(name="Hamburger").save()

        self.assertTrue(Team.objects.all().count() > 0)

        response = self.client.get(reverse('team-list'))

        for team in Team.objects.all():
            self.assertContains(response, team.__unicode__())

    def test_page_contains_links_to_teams(self):
        self.test_page_contains_all_teams()

        response = self.client.get(reverse('team-list'))

        for team in Team.objects.all():
            self.assertContains(response, reverse('team-detail', kwargs={'pk':team.pk}))

class DetailTeamsTests(TestCase):
    fixtures = ['test_data.json']

    def test_can_get_route(self):
        self.assertTrue(reverse('team-detail', kwargs={'pk':1}) != None)

    def test_can_load_page(self):
        response = self.client.get(reverse('team-detail', kwargs={'pk':1}))

        self.assertEqual(response.status_code, 200)

    def test_contains_team_name(self):
        team = Team.objects.get(pk=1)
        response = self.client.get(reverse('team-detail', kwargs={'pk':team.pk}))

        self.assertContains(response, team.__unicode__())

    def test_contains_list_of_owners(self):
        team = Team.objects.get(pk=1)
        response = self.client.get(reverse('team-detail', kwargs={'pk':team.pk}))

        for leader in team.owners():
            self.assertContains(response, leader.__unicode__())

    def test_private_team_is_not_open_to_public(self):
        team = Team(name="Team Awesome", private=True)
        team.save()

        response = self.client.get(reverse('team-detail', kwargs={'pk':team.pk}))

        self.assertEqual(response.status_code, 403)
