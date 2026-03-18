from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Society, Event, Ticket
from django.utils import timezone
from datetime import timedelta

class EventHubTests(TestCase):
    """
    Comprehensive test suite for the Event Hub application,
    covering models, views, and business logic.
    """

    def setUp(self):
        """Set up initial data for testing."""
        self.client = Client()
        
        # 1. Create a Student user
        self.student_user = User.objects.create_user(
            username='student@uog.com',
            email='student@uog.com',
            password='password123',
            role=User.STUDENT
        )
        
        # 2. Create an Admin user and a Society
        self.admin_user = User.objects.create_user(
            username='admin@uog.com',
            email='admin@uog.com',
            password='password123',
            role=User.SOCIETY_ADMIN
        )
        self.society = Society.objects.create(
            name="Test Society",
            admin=self.admin_user
        )
        
        # 3. Create a Test Event
        self.event = Event.objects.create(
            society=self.society,
            title="Test Workshop",
            description="A test event description.",
            location="Library Room 1",
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            capacity=2
        )

    # --- Model Tests ---

    def test_event_creation(self):
        """Test if the event was created correctly with the right attributes."""
        self.assertEqual(self.event.title, "Test Workshop")
        self.assertEqual(self.event.capacity, 2)

    def test_ticket_auto_code_generation(self):
        """Test if the Ticket model automatically generates a unique code on save."""
        ticket = Ticket.objects.create(user=self.student_user, event=self.event)
        self.assertTrue(ticket.ticket_code)
        self.assertEqual(len(ticket.ticket_code), 8)  # UUID split check

    # --- View & Logic Tests ---

    def test_home_page_requires_login(self):
        """Verify that the home page redirects unauthenticated users to login."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)

    def test_successful_booking_logic(self):
        """Test the booking process: Login -> View Detail -> Post Booking."""
        self.client.login(username='student@uog.com', password='password123')
        
        # Post to the event detail view to book a ticket
        response = self.client.post(reverse('event_detail', args=[self.event.id]))
        
        # Should redirect to 'my_tickets' after successful booking
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Ticket.objects.filter(user=self.student_user, event=self.event).exists())

    def test_capacity_limit_logic(self):
        """Ensure users cannot book tickets once the event capacity is reached."""
        # Fill capacity (Capacity is 2)
        user2 = User.objects.create_user(username='u2', password='p')
        user3 = User.objects.create_user(username='u3', password='p')
        Ticket.objects.create(user=self.student_user, event=self.event)
        Ticket.objects.create(user=user2, event=self.event)
        
        # Try to book with the 3rd user
        self.client.login(username='u3', password='p')
        response = self.client.post(reverse('event_detail', args=[self.event.id]))
        
        # Should NOT create a 3rd ticket
        self.assertEqual(Ticket.objects.filter(event=self.event).count(), 2)