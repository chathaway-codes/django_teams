from django.core.exceptions import PermissionDenied
# This is where your views go :)
from django.http import HttpResponseRedirect
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.db.models import Count, F
from django_teams.models import Team, TeamStatus, Ownership
from django_teams.forms import (TeamEditForm,
                                TeamStatusCreateForm,
                                action_formset)
from django.db.models import Case, When
from django.db import models
from django.contrib.contenttypes.models import ContentType


def loadGenericKeyRelations(queryset):
    distinct_contents = queryset.values_list('content_type', flat=True).distinct()
    object_items = []
    for object in distinct_contents:
        content_type = ContentType.objects.get(id=object).model_class()
        set = queryset.filter(content_type=object).values()
        objects = content_type.objects.filter(pk__in=[object['object_id'] for object in set])
        for relation in content_type._meta.get_fields():
            if relation.get_internal_type() is 'ForeignKey':
                objects.select_related(relation.name)
        object_items.append(objects.all())
    return object_items


class TeamListView(ListView):
    model = Team

    def render_to_response(self, context, **response_kwargs):
        queryset = Team.objects.all().annotate(member_count=Count('users'))
        queryset = queryset.annotate(owner=Case(When(teamstatus__role=20, then=F('users__username')), default=None))
        if not self.request.user.is_anonymous():
            queryset = queryset.annotate(role=Case(When(teamstatus__user=self.request.user,
                                         then=F('teamstatus__role')), default=0, outputfield=models.IntegerField()))
            queryset = queryset.order_by('-role')
        else:
            queryset = queryset.order_by('-id')
        team_names = []
        team_list = []
        # combine teams with the same name
        for q in queryset:
            if q.name not in team_names:
                team_names.append(q.name)
                tmp = {'name': q.name, 'id': q.id, 'pk': q.pk, 'description': q.description,
                       'member_count': q.member_count, 'owner': q.owner}
                try:
                    tmp['role'] = q.role
                except Exception:
                    tmp['role'] = None
                team_list.append(tmp)
            else:
                t = team_list[team_names.index(q.name)]
                t['member_count'] += q.member_count
                if q.owner is not None:
                    t['owner'] = q.owner
        return super(TeamListView, self).render_to_response({'list': team_list}, **response_kwargs)


class UserTeamListView(ListView):
    template_name = 'django_teams/user_team_list.html'

    def get_queryset(self):
        statuses = TeamStatus.objects.select_related('user').filter(user=self.request.user,
                                                                    role=20).values_list('team', flat=True)
        return statuses


class TeamCreateView(CreateView):
    model = Team
    template_name = 'django_teams/team_create.html'
    fields = ['name', 'description', 'private']

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return super(TeamCreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        ret = super(TeamCreateView, self).form_valid(form)
        self.object.add_user(self.request.user, team_role=20)
        return ret


class TeamDetailView(DetailView):
    model = Team

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return super(TeamDetailView, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        object = super(TeamDetailView, self).get_object(queryset)
        if object.private and self.request.user not in object.users.filter(teamstatus__role__gte=10):
            raise PermissionDenied()
        return object

    def render_to_response(self, context, **response_kwargs):
        team = self.object
        # context['owner'] = team.users.filter(teamstatus__role=20)
        # context['members'] = team.users.filter(teamstatus__role=10)
        context['owners'] = []
        context['members'] = []
        statuses = TeamStatus.objects.select_related('user', 'team').filter(team=team)
        for s in statuses:
            if s.role == 10:
                context['members'].append(s.user)
            elif s.role == 20:
                context['owners'].append(s.user)
        owned = Ownership.objects.filter(team=team, approved=True)
        context['approved_objects_types'] = loadGenericKeyRelations(owned)
        return super(TeamDetailView, self).render_to_response(context, **response_kwargs)


class TeamInfoEditView(UpdateView):
    model = Team
    fields = ['name', 'description', 'private']
    template_name = 'django_teams/teaminfo_form.html'

    def get_object(self, queryset=None):
        object = super(TeamInfoEditView, self).get_object(queryset)
        if self.request.user not in object.users.filter(teamstatus__role__gte=20):
            raise PermissionDenied()
        return object


class TeamEditView(UpdateView):
    model = Team
    form_class = TeamEditForm

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return super(TeamEditView, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        object = super(TeamEditView, self).get_object(queryset)

        # User must be admin of the object to get into this view
        if self.request.user not in object.users.filter(teamstatus__role__gte=20):
            raise PermissionDenied()
        return object

    def get_form_class(self):
        # get forms for team leaders, team members, team requests
        ret = []
        users = self.object.users
        ret += [action_formset(prefix_name='teachers', qset=users.filter(teamstatus__role=20),
                               actions=('---', 'Demote', 'Remove'))]
        ret += [action_formset(prefix_name='students', qset=users.filter(teamstatus__role=10),
                               actions=('---', 'Promote', 'Remove'))]
        ret += [action_formset(prefix_name='member-requests', qset=users.filter(teamstatus__role=1),
                               actions=('---', 'Approve', 'Reject'))]
        owned_objects = Ownership.objects.filter(team=self.object)
        approved = loadGenericKeyRelations(owned_objects.filter(approved=True))
        for set in approved:
            if set:
                prefix_name = 'approved-' + str(set.model.__name__)
                ret += [action_formset(prefix_name=prefix_name, qset=set, actions=('---', 'Remove'), link=True)]
        pending_approval = loadGenericKeyRelations(owned_objects.filter(approved=False))
        for set in pending_approval:
            if set:
                prefix_name = str(set.model.__name__) + 's-pending-approval'
                ret += [action_formset(prefix_name=prefix_name, qset=set,
                                       actions=('---', 'Approve', 'Remove'), link=True)]
        return ret

    def get_form(self, form_class=TeamEditForm):
        kwargs = self.get_form_kwargs()
        form_class = self.get_form_class()
        if 'data' in kwargs:
            ret = [form_class[num](kwargs['data'],
                                   prefix=form_class[num].name) for num in range(len(form_class))]
        else:
            ret = [form_class[num](prefix=form_class[num].name) for num in range(len(form_class))]

        return ret

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        self.object = get_object_or_404(Team, pk=kwargs['pk'])
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        for f in form:
            if not f.is_valid():
                return self.form_invalid(form)

        # Go through each form and perform the action
        # Owners
        owner_action = form[0].cleaned_data['action']
        owner_items = form[0].cleaned_data['items']
        if owner_action == 'Demote':
            for i in owner_items:
                o = self.object.get_user_status(i)
                o.role = 10
                o.save()
        if owner_action == 'Remove':
            for i in owner_items:
                self.object.get_user_status(i).delete()

        # Members
        member_action = form[1].cleaned_data['action']
        member_items = form[1].cleaned_data['items']
        if member_action == 'Promote':
            for i in member_items:
                o = self.object.get_user_status(i)
                o.role = 20
                o.save()
        if member_action == 'Remove':
            for i in member_items:
                self.object.get_user_status(i).delete()

        # Member Requests
        request_action = form[2].cleaned_data['action']
        request_items = form[2].cleaned_data['items']
        if request_action == 'Approve':
            for i in request_items:
                i.role = 10
                i.save()
        if request_action == 'Revoke':
            for i in request_items:
                i.delete()

        for num in range(3, len(form)):
            current_action = form[num].cleaned_data['action']
            current_items = form[num].cleaned_data['items']
            if current_action == 'Approve':
                for i in current_items:
                    i.approved = True
                    i.save()
            if current_action == 'Remove':
                for i in current_items:
                    i.delete()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('team-edit', kwargs={'pk': self.object.pk})


class TeamStatusCreateView(CreateView):
    model = TeamStatus
    form_class = TeamStatusCreateForm

    def get_success_url(self):
        return reverse('team-list')

    def dispatch(self, request, *args, **kwargs):
        self.team = Team.objects.get(pk=kwargs['team_pk'])
        self.request = request
        return super(TeamStatusCreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.team = self.team
        form.instance.user = self.request.user
        form.instance.role = 1
        return super(TeamStatusCreateView, self).form_valid(form)

    def render_to_response(self, context, **response_kwargs):
        context['team'] = self.team
        return super(TeamStatusCreateView, self).render_to_response(context, **response_kwargs)
