# This is where the models go!
import types
import sys
from django.db import models
from django.db.models.query import QuerySet
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist

# Using the user: user = models.ForeignKey(settings.AUTH_USER_MODEL)
CurrentUser = None
CurrentTeam = None

class Team(models.Model):
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='django_teams.TeamStatus')
    name = models.CharField(max_length=255)

    def add_user(self, user, team_role=1):
        TeamStatus(user=user, team=self, role=team_role).save()

    def approve_user(self, user):
        ts = TeamStatus.objects.get(user=user, team=self)
        if ts.role == 1:
            ts.role = 10
            ts.save()

class TeamStatus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    team = models.ForeignKey('django_teams.Team')

    TEAM_ROLES = (
        (1, 'Requesting Access'),
        (10, 'Team Member'),
        (20, 'Team Leader'),
    )

    role = models.IntegerField(choices=TEAM_ROLES)

class Ownership(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    team = models.ForeignKey('django_teams.Team')

    @staticmethod
    def grant_ownership(team, item):
        content_type = ContentType.objects.get_for_model(item)
        
        res = Ownership.objects.get_or_create(team=team, content_type=content_type, object_id=item.id)
        if res[1]:
            res[0].save()

def override_manager(model):
    def f(self):
      import django_teams.models
      if django_teams.models.CurrentUser == None:
          return QuerySet(model=self.model, using=self._db)
      else:
          # Get a list of objects on this model that the user has access too
          content_type = ContentType.objects.get_for_model(self.model)
          ownerships = None
          if django_teams.models.CurrentTeam != None:
              # If they are only invited to current team, raise an error
              if TeamStatus.objects.get(team=django_teams.models.CurrentTeam, user=django_teams.models.CurrentUser).role < 10:
                  raise ObjectDoesNotExist()
              ownerships = Ownership.objects.filter(content_type=content_type, team=django_teams.models.CurrentTeam)
          else:
              ownerships = Ownership.objects.filter(content_type=content_type, team__in=django_teams.models.CurrentUser.team_set.filter(teamstatus__role__gte=10))
          pk_list = []
          for o in ownerships:
              pk_list += [o.content_object.id]
          return QuerySet(model=self.model, using=self._db).filter(id__in=pk_list)
    model.objects.get_queryset = types.MethodType(f, model.objects)

def revert_manager(model):
    def f(self):
        return QuerySet(model=self.model, using=self._db)
    model.objects.get_queryset = types.MethodType(f, model.objects)
