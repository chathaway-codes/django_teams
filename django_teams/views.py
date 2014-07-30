from django.core.exceptions import PermissionDenied
# This is where your views go :)
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
#from django.contrib import messages

from django_teams.models import Team, Ownership, TeamStatus
from django_teams.forms import *

class TeamListView(ListView):
    model = Team

class TeamCreateView(CreateView):
    model = Team
    template_name = 'django_teams/team_create.html'

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

class TeamStatusCreateView(CreateView):
    model = TeamStatus

    def dispatch(self, request, *args, **kwargs):
        self.team = Team.objects.get(pk=kwargs['team_pk'])
        return super(TeamStatusCreateView, self).dispatch(request, *args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        context['team'] = self.team
        return super(TeamStatusCreateView, self).render_to_response(context, **response_kwargs)
