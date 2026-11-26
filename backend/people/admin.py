from django.contrib import admin

from .models import AdoptionApplication, GuardianRegistration


@admin.register(GuardianRegistration)
class GuardianRegistrationAdmin(admin.ModelAdmin):
    list_display = ('animal', 'person', 'status', 'created_at')
    list_filter = ('status',)
    list_select_related = ('animal', 'person__user')
    search_fields = ('animal__name', 'person__user__username')
    ordering = ('-created_at',)


@admin.register(AdoptionApplication)
class AdoptionApplicationAdmin(admin.ModelAdmin):
    list_display = ('animal', 'person', 'status', 'created_at')
    list_filter = ('status',)
    list_select_related = ('animal', 'person__user')
    search_fields = ('animal__name', 'person__user__username')
    ordering = ('-created_at',)
