from functools import wraps
from django_teams.models import override_manager, revert_manager
import django_teams.models
from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import available_attrs
from django.db import models
from django_teams.utils import get_related_managers

import sys
import inspect

def teamify(view_func):
    @wraps(view_func, assigned=available_attrs(view_func))
    def wrapper(request, *args, **kwargs):
        # Set the current user
        django_teams.models.CurrentUser = request.user
        # Set the current team, as per settings instructions
        def get_team(user, **kwargs):
            if 'django_team_pk' in kwargs:
                return Team.objects.get(pk=kwargs['django_team_pk'])
            return None

        django_teams.models.CurrentTeam = get_team(django_teams.models.CurrentUser, **kwargs)

        # Setup the filters
        # Ignore apps/models specified in settings
        ignore_apps = ['django_teams', 'contenttypes']
        ignore_models = []
        for model in models.get_models(include_auto_created=True):
            m = ContentType.objects.get_for_model(model)
            if m.app_label not in ignore_apps and (m.app_label + '_' + m.model) not in ignore_models:
                override_manager(model)
                # Override related managers
                for manager in get_related_managers(model):
                    sys.stdout.write(repr(manager)+"\n")
                    sys.stdout.flush()
                    override_manager(manager)

        try:
            ret = view_func(request, *args, **kwargs)
        finally:
            for model in models.get_models(include_auto_created=True):
                revert_manager(model)
        return ret
    return wrapper
