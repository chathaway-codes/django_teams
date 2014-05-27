# This is where the models go!
from django.db import models
from django.core.urlresolvers import reverse
from django.conf import settings

# Using the user: user = models.ForeignKey(settings.AUTH_USER_MODEL)

class Team(models.Model):
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='django_teams.TeamStatus')
    name = models.CharField(max_length=255)

    def add_user(self, user, team_role=1):
        TeamStatus(user=user, team=self, role=team_role).save()

class TeamStatus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    team = models.ForeignKey('django_teams.Team')

    TEAM_ROLES = (
        (1, 'Requesting Access'),
        (10, 'Team Member'),
        (20, 'Team Leader'),
    )

    role = models.IntegerField(choices=TEAM_ROLES)
