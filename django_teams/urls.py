from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

from django_teams.views import *

urlpatterns = patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    # TemplateView + Login
    #url(r'^$', login_required(TemplateView.as_view(template_name="home.html")), {}, 'home'),
    url(r'^teams/$', TeamListView.as_view(), name='team-list'),
    url(r'^teams/create$', TeamCreateView.as_view(), name='team-create'),
    url(r'^teams/(?P<team_pk>\d+)/invite$', TeamStatusCreateView.as_view(), name='teamstatus-create'),
    url(r'^teams/(?P<pk>\d+)/$', TeamDetailView.as_view(), name='team-detail'),
    url(r'^teams/(?P<pk>\d+)/edit$', TeamEditView.as_view(), name='team-edit'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )
