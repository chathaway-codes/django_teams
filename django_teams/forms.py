from django.forms import ModelForm

from django_teams.models import Team

class TeamEditForm(ModelForm):
    class Meta:
        model = Team
