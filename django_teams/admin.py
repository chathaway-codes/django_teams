# This is where you can add stuff to the admin view
from django.contrib import admin

from django_teams.models import Team, TeamStatus, Ownership

# ie,
# admin.site.register(User, UserAdmin)
admin.site.register(Team)
admin.site.register(TeamStatus)
admin.site.register(Ownership)
