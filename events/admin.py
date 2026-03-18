from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Society, Event, Ticket, Review

# --- User Admin Customization ---
class CustomUserAdmin(UserAdmin):
    """
    Customizing the User Admin interface to include project-specific fields 
    like roles and profile pictures.
    """
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Info', {'fields': ('role', 'profile_picture', 'phone_number')}),
    )
    list_display = ['username', 'email', 'role', 'is_staff']

# Registering the custom User model with the customized admin class
admin.site.register(User, CustomUserAdmin)

# --- Society Admin Configuration ---
@admin.register(Society)
class SocietyAdmin(admin.ModelAdmin):
    """
    Admin configuration for Societies, allowing admins to search by name 
    and view creation dates.
    """
    list_display = ('name', 'admin', 'created_at')
    search_fields = ('name',)

# --- Event Admin Configuration ---
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Admin interface for Events with built-in filtering by society and time 
    to manage large amounts of campus activities efficiently.
    """
    list_display = ('title', 'society', 'start_time', 'location', 'capacity')
    list_filter = ('society', 'start_time')
    search_fields = ('title', 'location')

# --- Ticket Admin Configuration ---
@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """
    Management interface for Tickets. Ticket codes are set to read-only 
    to prevent accidental modification of unique identifiers.
    """
    list_display = ('ticket_code', 'event', 'user', 'status', 'purchased_at')
    list_filter = ('status', 'event')
    readonly_fields = ('ticket_code',)

# Registering Review model with default admin settings
admin.site.register(Review)