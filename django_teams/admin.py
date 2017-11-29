# This is where you can add stuff to the admin view
from django.contrib import admin

from django_teams.models import Team, TeamStatus, Ownership


class TeamAdmin(admin.ModelAdmin):
    """Innumerate application updating from admin."""

    list_display = ['name', 'description', 'owner', 'member']
    search_fields = ['name', 'users__username']

    def owner(self, obj):
        return "\n".join([a.username for a in obj.owners().all()])

    def member(self, obj):
        return "\n".join([a.username for a in obj.members().all()])


class TeamStatusAdmin(admin.ModelAdmin):
    """Innumerate application updating from admin."""

    list_display = ['user', 'team', 'comment', 'role']
    search_fields = ['user__username', 'team__name']
    list_filter = ['role']


class OwnershipAdmin(admin.ModelAdmin):
    """Innumerate application updating from admin."""

    list_display = ['content_object', 'owner', 'team', 'approved', 'content_type']
    search_fields = ['team__name']
    list_filter = ['approved']

    def owner(self, obj):
        if hasattr(obj.content_object, 'owner'):
            return obj.content_object.owner
        return 'n/a'


# ie,
# admin.site.register(User, UserAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(TeamStatus, TeamStatusAdmin)
admin.site.register(Ownership, OwnershipAdmin)
