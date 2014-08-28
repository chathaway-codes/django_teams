from django.core.exceptions import PermissionDenied
# This is where your views go :)
from django.http import HttpResponseRedirect
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.core.urlresolvers import reverse
#from django.contrib import messages
from django.shortcuts import get_object_or_404

from django_teams.models import Team, Ownership, TeamStatus
from django_teams.forms import *

class TeamListView(ListView):
    model = Team

class TeamCreateView(CreateView):
    model = Team
    template_name = 'django_teams/team_create.html'
    fields = ['name', 'private']

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
        ret += [action_formset(self.object.owners(), ('---', 'Demote', 'Remove'))]
        ret += [action_formset(self.object.members(), ('---', 'Promote', 'Remove'))]
        ret += [action_formset(self.object.requests(), ('---', 'Approve', 'Revoke'))]
        return ret

    def get_form(self, form_class):
        kwargs = self.get_form_kwargs()
        if 'data' in kwargs:
            ret = [form_class[0](kwargs['data'], prefix='owners'), form_class[1](kwargs['data'], prefix='members'), form_class[2](kwargs['data'], prefix='requests')]
        else:
            ret = [form_class[0](prefix='owners'), form_class[1](prefix='members'), form_class[2](prefix='requests')]

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
        print "owner_action: %s" % repr(owner_action)
        print "owner_items: %s" % repr(owner_items)
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

        # Requests
        request_action = form[2].cleaned_data['action']
        request_items = form[2].cleaned_data['items']
        if request_action == 'Approve':
            for i in request_items:
                i.role = 10
                i.save()
        if request_action == 'Revoke':
            for i in request_items:
                i.delete()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
      return reverse('team-edit', kwargs={'pk':self.object.pk})

class TeamStatusCreateView(CreateView):
    model = TeamStatus

    def dispatch(self, request, *args, **kwargs):
        self.team = Team.objects.get(pk=kwargs['team_pk'])
        return super(TeamStatusCreateView, self).dispatch(request, *args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        context['team'] = self.team
        return super(TeamStatusCreateView, self).render_to_response(context, **response_kwargs)
