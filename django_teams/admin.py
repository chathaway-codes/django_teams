# This is where you can add stuff to the admin view
from django.contrib import admin
from django.conf.urls import url
from django.http import HttpResponse
from django_teams.models import Team, TeamStatus, Ownership
from django.db.models import Count
from django.db import models

# ie,
# admin.site.register(User, UserAdmin)
#admin.site.register(Team)
#admin.site.register(TeamStatus)
#admin.site.register(Ownership)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):

	show_full_result_count = False


@admin.register(Ownership)
class OwnershipAdmin(admin.ModelAdmin):

	show_full_result_count = False


@admin.register(TeamStatus)
class TeamStatusAdmin(admin.ModelAdmin):

	show_full_result_count = False

	def get_queryset(self, request):
		qs = super(TeamStatusAdmin, self).get_queryset(request)
		return qs.select_related('user', 'team').filter(user=request.user)