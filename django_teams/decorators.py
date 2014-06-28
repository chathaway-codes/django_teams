from functools import wraps
from django_teams.models import override_manager, revert_manager
from django_teams.models import CurrentUser, CurrentTeam
from django.utils.decorators import available_attrs
from django.db import models

def teamify(view_func):
    @wraps(view_func, assigned=available_attrs(view_func))
    def wrapper(request, *args, **kwargs):
        # Set the current user
        CurrentUser = request.user
        # Set the current team, as per settings instructions
        def get_team(user, **kwargs):
            if django_team_pk in kwargs:
                return Team.objects.get(pk=kwargs['django_team_pk'])
            return None

        CurrentTeam = get_team(CurrentUser, **kwargs)

        # Setup the filters
        # Ignore apps/models specified in settings
        ignore_apps = ['django_teams', 'contenttypes']
        ignore_models = []
        for model in models.get_models(include_auto_created=True):
            m = ContentType.objects.get_for_model(model)
            if m.app_label not in ignore_apps and (m.app_label + '_' + m.model) not in ignore_models:
                override_manager(model)

        try:
            ret = view_func(request, *args, **kwargs)
        finally:
            for model in models.get_models(include_auto_created=True):
                revert_manager(model)
        return ret
    return wrapper
