# This is where the models go!
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

# Using the user: user = models.ForeignKey(settings.AUTH_USER_MODEL)
CurrentUser = None
CurrentTeam = None


class Team(models.Model):
    users = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                   blank=True,
                                   through='django_teams.TeamStatus',
                                   related_name='team_member')
    name = models.CharField(max_length=255)
    private = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)

    def get_absolute_url(self):
        return reverse('team-detail', kwargs={'pk': self.pk})

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

        # I'm pretty sure there's a django one liner for this but I don't feel like looking right now
        # Someone might want to do that in the future
        for ownership in Ownership.objects.filter(team=self, content_type=contenttype):
            ret += [ownership.content_object]

        return ret

    def unapproved_objects(self):
        return Ownership.objects.filter(team=self, approved=False)

    def approved_objects(self):
        return Ownership.objects.filter(team=self, approved=True)

    def approved_objects_of_model(self, model):
        # Maybe not the best way
        contenttype = ContentType.objects.get_for_model(model)
        ret = []

        # I'm pretty sure there's a django one liner for this but I don't feel like looking right now
        # Someone might want to do that in the future
        for ownership in Ownership.objects.filter(team=self, content_type=contenttype, approved=True):
            ret += [ownership.content_object]

        return ret

    def owned_object_types(self):
        ret = []
        for ownership in Ownership.objects.filter(team=self):
            if ownership.content_type.model_class() not in ret:
                ret += [ownership.content_type.model_class()]
        return ret

    def member_count(self):
        return self.users.all().count()

    def get_user_status(self, user):
        s = TeamStatus.objects.filter(user=user, team=self)
        if len(s) >= 1:
            return s[0]
        return None

    def approve_user(self, user):
        ts = TeamStatus.objects.get(user=user, team=self)
        if ts.role == 1:
            ts.role = 10
            ts.save()

    @staticmethod
    def get_current_team():
        if CurrentTeam is not None:
            return CurrentTeam
        return None


class TeamStatus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    team = models.ForeignKey('django_teams.Team', on_delete=models.CASCADE)
    comment = models.CharField(max_length=255, default='', null=True, blank=True)

    TEAM_ROLES = (
        (1, 'Requesting Access'),
        (10, 'Team Member'),
        (20, 'Team Leader'),
    )

    role = models.IntegerField(choices=TEAM_ROLES)

    def approve(self):
        self.role = 10
        self.save()

    def __unicode__(self):
        return "%s requesting to join %s" % (self.user.__unicode__(), self.team.__unicode__())


class Ownership(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    approved = models.BooleanField(default=False)
    team = models.ForeignKey('django_teams.Team', on_delete=models.CASCADE)

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
