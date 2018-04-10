# This is where you can add stuff to the admin view
from django.contrib import admin
from django_teams.models import Team, TeamStatus, Ownership
from django.contrib.auth.models import Group, User


admin.site.unregister(Group)
admin.site.unregister(User)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):

    show_full_result_count = False


@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    show_full_result_count = False


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):

    show_full_result_count = False

    def get_queryset(self, request):
        qs = super(TeamAdmin, self).get_queryset(request)
        return qs.select_related()


@admin.register(Ownership)
class OwnershipAdmin(admin.ModelAdmin):

    show_full_result_count = False

    def get_queryset(self, request):
        qs = super(OwnershipAdmin, self).get_queryset(request)
        return qs.select_related()


@admin.register(TeamStatus)
class TeamStatusAdmin(admin.ModelAdmin):

    show_full_result_count = False

    def get_queryset(self, request):
        qs = super(TeamStatusAdmin, self).get_queryset(request)
        return qs.select_related('user', 'team').filter(user=request.user)
