from django.core.exceptions import PermissionDenied
# This is where your views go :)
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
#from django.views.generic.edit import CreateView, UpdateView
#from django.contrib import messages

from django_teams.models import Team, Ownership

class TeamListView(ListView):
    model = Team

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
