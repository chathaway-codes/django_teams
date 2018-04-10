from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views import static
from django_teams.views import (TeamListView, UserTeamListView,
                                TeamCreateView, TeamDetailView,
                                TeamInfoEditView, TeamEditView,
                                TeamStatusCreateView)

from django.contrib import admin
admin.autodiscover()


urlpatterns = [
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^teams/$', TeamListView.as_view(), name='team-list'),
    url(r'^my-teams/$', login_required(UserTeamListView.as_view()), name='user-team-list'),
    url(r'^teams/create$', login_required(TeamCreateView.as_view()), name='team-create'),
    url(r'^teams/(?P<team_pk>\d+)/invite$', login_required(TeamStatusCreateView.as_view()), name='teamstatus-create'),
    url(r'^teams/(?P<pk>\d+)/$', TeamDetailView.as_view(), name='team-detail'),
    url(r'^teams/(?P<pk>\d+)/edit$', TeamEditView.as_view(), name='team-edit'),
    url(r'^teams/(?P<pk>\d+)/info/edit$', TeamInfoEditView.as_view(), name='team-info-edit'),
]

if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', static.serve,
            {'document_root': settings.MEDIA_ROOT, }), ]
