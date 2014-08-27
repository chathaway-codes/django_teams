from django.core.exceptions import PermissionDenied
# This is where your views go :)
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
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
        print "kwargs: %s" % repr(kwargs)
        owner_objects = {'prefix': 'owners'}
        member_objects = {'prefix': 'members'}
        requests_objects = {'prefix': 'requests'}
        if 'data' in kwargs:
            for key, value in kwargs['data'].iteritems():
                if key.split('-')[0] == 'owners':
                    owner_objects[key.split('-')] = value
                if key.split('-')[0] == 'members':
                    member_objects[key.split('-')] = value
                if key.split('-')[0] == 'requests':
                    requests_objects[key.split('-')] = value
        print "owner_objects: %s" % repr(owner_objects)
        ret = [form_class[0](**owner_objects), form_class[1](**member_objects), form_class[2](**requests_objects)]

        return ret

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        self.object = get_object_or_404(Team, pk=kwargs['pk'])
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        print "Here1"

        for f in form:
            print "in form %s" % repr(f)
            if not f.is_valid():
                print "form not valid %s" % repr (f)
                print vars(f)
                return self.form_invalid(form)
        # Go through each form and perform the action
        # Owners
        print "Here2"
        owner_action = form[0].cleaned_data['action']
        owner_items = form[0].cleaned_data['items']
        if owner_action == 'Demote':
            for i in owner_items:
                self.oject.get_user_status(i).role = 10
        if owner_action == 'Remove':
            for i in owner_items:
                self.object.get_user_status(i).delete()

        # Members
        member_action = form[1].cleaned_data['action']
        member_items = form[1].cleaned_data['items']
        if member_action == 'Promote':
            for i in member_items:
                self.oject.get_user_status(i).role = 20
        if member_action == 'Remove':
            for i in member_items:
                self.object.get_user_status(i).delete()

        # Requests
        request_action = form[0].cleaned_data['action']
        request_items = form[0].cleaned_data['items']
        if request_action == 'Approve':
            print "Here"
            for i in request_items:
                self.oject.add_user(i)
        if request_action == 'Revoke':
            for i in request_items:
                i.delete()

        return self.form_valid(form)

class TeamStatusCreateView(CreateView):
    model = TeamStatus

    def dispatch(self, request, *args, **kwargs):
        self.team = Team.objects.get(pk=kwargs['team_pk'])
        return super(TeamStatusCreateView, self).dispatch(request, *args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        context['team'] = self.team
        return super(TeamStatusCreateView, self).render_to_response(context, **response_kwargs)
