from django import template
from django.contrib.contenttypes.models import ContentType


def get_user_status(team, user):
    ts = team.get_user_status(user)
    return ts


def get_owned_objects(team, model):
    return team.owned_objects(model)


def get_approved_objects(team, model):
    return team.approved_objects_of_model(model)


def verbose_name(object):
    return object._meta.verbose_name


def load_fragment_template(object):
    ct = ContentType.objects.get_for_model(object)
    template_name = 'django_teams/fragments/%s/%s.html' % (ct.app_label, ct.model)
    try:
        template.loader.get_template(template_name)
        return template_name
    except template.TemplateDoesNotExist:
        return "django_teams/fragments/default.html"


def get(object, name):
    return getattr(object, name)


register = template.Library()
register.filter(get_user_status)
register.filter(get_owned_objects)
register.filter(get_approved_objects)
register.filter(verbose_name)
register.filter(load_fragment_template)
register.filter(get)
