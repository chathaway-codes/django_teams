from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_teams.models import Team, TeamStatus, Ownership


class ListTeamsTests(TestCase):
    fixtures = ['test_data.json']

    def test_can_get_route(self):
        self.assertTrue(reverse('team-list') is not None)

    def test_can_load_page(self):
        response = self.client.get(reverse('team-list'))

        self.assertEqual(response.status_code, 200)

    def test_page_contains_all_teams(self):
        # Team(name="Team Awesome").save()
        # Team(name="Team Silly").save()
        # Team(name="Hamburger").save()

        Team(name='team1').save()
        Team(name='team2').save()
        Team(name='team3').save()
        self.assertTrue(Team.objects.all().count() > 0)

        response = self.client.get(reverse('team-list'))

        for team in Team.objects.all():
            self.assertContains(response, str(team))

    def test_page_contains_links_to_teams(self):
        self.test_page_contains_all_teams()

        response = self.client.get(reverse('team-list'))

        for team in Team.objects.all():
            self.assertContains(response, reverse('team-detail', kwargs={'pk': team.pk}))


class DetailTeamsTests(TestCase):
    fixtures = ['test_data.json']

    def test_can_get_route(self):
        self.assertTrue(reverse('team-detail', kwargs={'pk': 1}) is not None)

    def test_can_load_page(self):
        response = self.client.get(reverse('team-detail', kwargs={'pk': 1}))

        self.assertEqual(response.status_code, 200)

    def test_contains_team_name(self):
        team = Team.objects.get(pk=1)
        response = self.client.get(reverse('team-detail', kwargs={'pk': team.pk}))

        self.assertContains(response, str(team))

    def test_contains_list_of_owners(self):
        team = Team.objects.get(pk=1)
        response = self.client.get(reverse('team-detail', kwargs={'pk': team.pk}))
        owners = team.users.filter(teamstatus__role=20)
        for leader in owners:
            self.assertContains(response, str(leader))

    def test_private_team_is_not_open_to_public(self):
        team = Team(name="Team Awesome", private=True)
        team.save()

        response = self.client.get(reverse('team-detail', kwargs={'pk': team.pk}))

        self.assertEqual(response.status_code, 403)


class EditTeamsTests(TestCase):
    fixtures = ['test_data.json']

    def test_can_get_route(self):
        self.assertTrue(reverse('team-edit', kwargs={'pk': 1}) is not None)

    def test_can_tell_admin_page(self):
        """Verify text asserting that this is the admin page
        """
        team = Team(name="Team Awesome")
        team.save()

        user = User.objects.get(pk=1)
        team.add_user(user, team_role=20)

        self.client.login(username='test', password='test')
        response = self.client.get(reverse('team-edit', kwargs={'pk': team.pk}))
        self.client.logout()

        self.assertContains(response, str(team))
        self.assertContains(response, "admin")

    def test_non_leader_cant_access_page(self):
        """Non-admin users should not be able to access this page at all
        """
        team = Team(name="Team Awesome")
        team.save()

        user = User.objects.get(pk=1)
        team.add_user(user, team_role=10)

        self.client.login(username='test', password='test')

        response = self.client.get(reverse('team-edit', kwargs={'pk': team.pk}))

        self.assertEqual(response.status_code, 403)

        self.client.logout()

    def test_can_post_page(self):
        """Verify that we can post changes to an admin page;
        for example, approve users
        """
        pass

    def test_can_tell_admin_info_page(self):
        """Verify that we can access the update info page
        """
        team = Team(name="Team Awesome")
        team.save()

        user = User.objects.get(pk=1)
        team.add_user(user, team_role=20)

        self.client.login(username='test', password='test')
        self.client.get(reverse('team-info-edit', kwargs={'pk': team.pk}))
        self.client.logout()

    def test_non_leader_cant_access_info_page(self):
        """Non-admin users should not be able to access this page at all
        """
        team = Team(name="Team Awesome")
        team.save()

        user = User.objects.get(pk=1)
        team.add_user(user, team_role=10)

        self.client.login(username='test', password='test')

        response = self.client.get(reverse('team-info-edit', kwargs={'pk': team.pk}))

        self.assertEqual(response.status_code, 403)

        self.client.logout()

class AdminTests(TestCase):
    fixtures = ['test_data.json']

    def test_team(self):
        Team(name='team1').save()
        Team(name='team2').save()
        Team(name='team3').save()
        self.assertTrue(Team.objects.all().count() > 0)
        self.client.login(username='test', password='test')
        response = self.client.get('/admin/django_teams/team/')
        for team in Team.objects.all():
            self.assertContains(response, str(team))
        self.client.logout()

    def test_ownership(self):
        Ownership(object_id=5, content_type_id=5, team_id=5).save()
        Ownership(object_id=6, content_type_id=6, team_id=6).save()
        Ownership(object_id=7, content_type_id=7, team_id=7).save()
        self.assertTrue(Ownership.objects.all().count() > 0)
        self.client.login(username='test', password='test')
        response = self.client.get('/admin/django_teams/ownership/')
        for ownership in Ownership.objects.all():
            self.assertContains(response, str(ownership))
        self.client.logout()

    def test_teamstatus(self):
        TeamStatus(team_id=5, user_id=1, role=10).save()
        TeamStatus(team_id=6, user_id=1, role=20).save()
        TeamStatus(team_id=7, user_id=1, role=10).save()
        self.assertTrue(Ownership.objects.all().count() > 0)
        self.client.login(username='test', password='test')
        response = self.client.get('/admin/django_teams/teamstatus/')
        for teamstatus in TeamStatus.objects.all():
            if teamstatus.user_id == 1:
                self.assertContains(response, str(teamstatus))
        self.client.logout()