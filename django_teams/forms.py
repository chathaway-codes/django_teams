from django.forms import ModelForm
from django import forms
from django_teams.models import Team, TeamStatus


class TeamCreateForm(ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description', 'private']


class TeamEditForm(ModelForm):
    """This form is very complicated;
    it consists of a hash containing :
        An array of pending requests
        An array of team leaders
        An array of team members
    The form should allow the team leaders to perform the following
    actions on any number of elements from each array, at the same time:
        Pending requests;
            approve
            deny
        Team Leaders
            Demote
            Remove
        Team Members
            Promote
            Remove
    """

    class Meta:
        model = Team
        fields = ['users', 'name', 'description', 'private']


class TeamStatusCreateForm(ModelForm):
    class Meta:
        model = TeamStatus
        fields = ['comment']


def action_formset(prefix_name, qset, actions, link=False):
    """A form factory which returns a form which allows the user to pick a specific action to
    perform on a chosen subset of items from a queryset.
    """
    class _ActionForm(forms.Form):
        name = prefix_name
        queryset = qset
        items = forms.ModelMultipleChoiceField(queryset=qset, required=False)
        action = forms.ChoiceField(choices=zip(actions, actions), required=False)

    return _ActionForm
