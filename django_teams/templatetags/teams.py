from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from django_teams.models import Team, TeamStatus, Ownership

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
    print template.loader.get_template(template_name)
    try:
        return template.loader.get_template(template_name)
    except template.TemplateDoesNotExist:
        return "django_teams/fragments/default.html"
		
def get_src(object):
    try:
        ct = ContentType.objects.get_for_id(object.content_type_id)
        obj = ct.get_object_for_this_type(id=object.object_id)
        return obj
    except:
        return object

def get(object, name):
  return getattr(object, name)

register = template.Library()
register.filter('get_user_status',get_user_status)
register.filter('get_owned_objects',get_owned_objects)
register.filter('get_approved_objects',get_approved_objects)
register.filter('verbose_name',verbose_name)
register.filter('load_fragment_template',load_fragment_template)
register.filter('get_src',get_src)
register.filter('get',get)
