# This is where the models go!
import types
import inspect
import sys
from django.db import models
from django.db.models.query import QuerySet
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields.related import SingleRelatedObjectDescriptor

# Using the user: user = models.ForeignKey(settings.AUTH_USER_MODEL)
CurrentUser = None
CurrentTeam = None

class Team(models.Model):
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='django_teams.TeamStatus')
    name = models.CharField(max_length=255)
    private = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def add_user(self, user, team_role=1):
        TeamStatus(user=user, team=self, role=team_role).save()

    def owners(self):
        return self.users.filter(teamstatus__role=20)

    def members(self):
        return self.users.filter(teamstatus__role=10)

    def requests(self):
        return TeamStatus.objects.filter(team=self, role=1)

    def owned_objects(self, model):
        # Maybe not the best way
        contenttype = ContentType.objects.get_for_model(model)
        ret = []
        for ownership in Ownership.objects.filter(team=self, content_type=contenttype):
            ret += [ownership.content_object]
        return ret

    def owned_object_types(self):
        ret = []
        for ownership in Ownership.objects.filter(team=self):
            ret += [ownership.content_type.model_class()]
        return ret

    def member_count(self):
        return self.users.all().count()

    def get_user_status(self, user):
        return TeamStatus.objects.filter(user=user, team=self)

    def approve_user(self, user):
        ts = TeamStatus.objects.get(user=user, team=self)
        if ts.role == 1:
            ts.role = 10
            ts.save()

    @staticmethod
    def get_current_team():
        if CurrentTeam != None:
            return CurrentTeam
        return None


class TeamStatus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    team = models.ForeignKey('django_teams.Team')
    comment = models.CharField(max_length=255, default='')

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
    def check_permission(item):
        content_type = ContentType.objects.get_for_model(item)
        res = Ownership.objects.filter(team=Team.get_current_team(), content_type=content_type, object_id=item.id)

        return len(res) > 0

    @staticmethod
    def grant_ownership(team, item):
        content_type = ContentType.objects.get_for_model(item)

        res = Ownership.objects.get_or_create(team=team, content_type=content_type, object_id=item.id)
        if res[1]:
            res[0].save()

def override_manager(model):
    def f(self):
      import django_teams.models
      #sys.stdout.write("In overridemanager for "+repr(self.model)+"\n")
      #sys.stdout.write(repr(dir(self)))
      #sys.stdout.write("\n")
      #sys.stdout.flush()
      if django_teams.models.CurrentUser == None:
          return QuerySet(model=self.model, using=self._db)
      else:
          # Get a list of objects on this model that the user has access too
          content_type = ContentType.objects.get_for_model(self.model)
          pk_list = None
          if django_teams.models.CurrentTeam != None:
              # If they are only invited to current team, raise an error
              if TeamStatus.objects.get(team=django_teams.models.CurrentTeam, user=django_teams.models.CurrentUser).role < 10:
                  raise ObjectDoesNotExist()
              pk_list = Ownership.objects.values_list("object_id", flat=True).filter(content_type=content_type, team=django_teams.models.CurrentTeam)
          else:
              pk_list = Ownership.objects.values_list("object_id", flat=True).filter(content_type=content_type, team__in=django_teams.models.CurrentUser.team_set.filter(teamstatus__role__gte=10))
          return QuerySet(model=self.model, using=self._db).filter(pk__in=pk_list)
    #sys.stdout.write("Overriding "+repr(model)+"\n")
    #sys.stdout.flush()
    if inspect.isclass(model) and issubclass(model, models.Model):
        model.objects._get_queryset = model.objects.get_queryset
        model.objects.get_queryset = types.MethodType(f, model.objects)
    elif type(model) is not SingleRelatedObjectDescriptor:
        try:
            model.related_manager_cls._get_queryset = model.related_manager_cls.get_queryset
            model.related_manager_cls.get_queryset = types.MethodType(f, model.related_manager_cls)
        except:
            pass

def revert_manager(model):
    if hasattr(model.objects, '_get_queryset'):
        if issubclass(model, models.Model):
            model.objects.get_queryset = model.objects._get_queryset
        elif type(model) is not SingleRelatedObjectDescriptor:
            try:
                model.related_manager_cls.get_queryset = model.related_manager_cls._get_queryset
            except:
                pass
