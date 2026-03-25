from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid

# --- Custom User Model ---
class User(AbstractUser):
    """
    Extending the default Django User model to distinguish between 
    students and society administrators.
    """
    STUDENT = 'student'
    SOCIETY_ADMIN = 'society_admin'
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (SOCIETY_ADMIN, 'Society Admin'),
    ]

    # Additional fields to support specific project requirements
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=STUDENT)
    profile_picture = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

# --- Society Model ---
class Society(models.Model):
    """
    Represents a University Society. Each society is managed by exactly 
    one User (Society Admin).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    logo = models.ImageField(upload_to='society_logos/', blank=True, null=True)
    
    # One-to-One relationship ensures a unique manager for each society
    admin = models.OneToOneField(User, on_delete=models.CASCADE, related_name='managed_society')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# --- Event Model ---
class Event(models.Model):
    """
    Core model for campus events, including logistical details like location and capacity.
    """
    society = models.ForeignKey(Society, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255)
    
    # Fields for potential Map API integration
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.PositiveIntegerField()
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# --- Ticket Model ---
class Ticket(models.Model):
    """
    Handles event bookings. Each ticket generates a unique code automatically upon creation.
    """
    STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('used', 'Used'),
        ('cancelled', 'Cancelled'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_tickets')
    ticket_code = models.CharField(max_length=50, unique=True, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='valid')
    purchased_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Overriding the save method to generate a short, unique ticket identifier 
        using UUID if one does not already exist.
        """
        if not self.ticket_code:
            self.ticket_code = str(uuid.uuid4()).split('-')[0].upper()
        super().save(*args, **kwargs)

    def _resolved_status_key(self, current_time=None):
        """Calculates the live ticket state from the booking status and event window."""
        current_time = current_time or timezone.now()

        if self.status == 'cancelled':
            return 'cancelled'
        if self.status == 'used':
            return 'used'
        if current_time < self.event.start_time:
            return 'upcoming'
        if current_time >= self.event.end_time:
            return 'expired'
        return 'valid'

    @property
    def display_status(self):
        """Returns the user-facing status, including the event access window."""
        return {
            'valid': 'Valid',
            'upcoming': 'Upcoming',
            'used': 'Used',
            'expired': 'Expired',
            'cancelled': 'Cancelled',
        }[self.display_status_key]

    @property
    def display_status_key(self):
        """Returns a normalized status key for styling in templates."""
        return self._resolved_status_key()

    @property
    def is_qr_active(self):
        """A QR code should only be scannable while the event is in progress."""
        return self.display_status_key == 'valid'

    @property
    def entry_pass_caption(self):
        """Short label shown under the ticket QR area."""
        return {
            'valid': 'Scan for Entry',
            'upcoming': 'Available at Start Time',
            'used': 'Already Checked In',
            'expired': 'Entry Closed',
            'cancelled': 'Ticket Cancelled',
        }[self.display_status_key]

    @property
    def entry_pass_note(self):
        """Context explaining whether the QR code can be used right now."""
        return {
            'valid': 'Present this QR code or reference code at check-in.',
            'upcoming': 'This QR code will activate when the event begins.',
            'used': 'This ticket has already been scanned at check-in.',
            'expired': 'This event has ended, so the QR code is no longer valid.',
            'cancelled': 'This booking has been cancelled and can no longer be used.',
        }[self.display_status_key]

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"

# --- Review Model ---
class Review(models.Model):
    """
    Allows students to rate and review events. 
    A unique_together constraint ensures a user can only review an event once.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevents multiple reviews from the same user on the same event
        unique_together = ('event', 'user')
