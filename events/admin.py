from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Society, Event, Ticket, Review

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Info', {'fields': ('role', 'profile_picture', 'phone_number')}),
    )
    list_display = ['username', 'email', 'role', 'is_staff']

admin.site.register(User, CustomUserAdmin)

@admin.register(Society)
class SocietyAdmin(admin.ModelAdmin):
    list_display = ('name', 'admin', 'created_at')
    search_fields = ('name',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'society', 'start_time', 'location', 'capacity')
    list_filter = ('society', 'start_time')
    search_fields = ('title', 'location')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_code', 'event', 'user', 'status', 'purchased_at')
    list_filter = ('status', 'event')
    readonly_fields = ('ticket_code',)

admin.site.register(Review)