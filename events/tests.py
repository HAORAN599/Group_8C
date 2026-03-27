from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Society, Event, Ticket
from .forms import EventForm
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
            role=User.STUDENT,
            phone_number='07111111111'
        )
        
        # 2. Create an Admin user and a Society
        self.admin_user = User.objects.create_user(
            username='admin@uog.com',
            email='admin@uog.com',
            password='password123',
            role=User.SOCIETY_ADMIN,
            phone_number='07222222222'
        )
        self.society = Society.objects.create(
            name="Test Society",
            description="A test society.",
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

    def test_landing_page_is_public(self):
        """The public landing page should be reachable without authentication."""
        response = self.client.get(reverse('landing'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'University Society Event Hub')

    def test_successful_booking_logic(self):
        """Test the booking process: Login -> View Detail -> Post Booking."""
        self.client.login(username='student@uog.com', password='password123')
        
        # Post to the event detail view to book a ticket
        response = self.client.post(reverse('event_detail', args=[self.event.id]))
        
        # Should redirect to 'my_tickets' after successful booking
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Ticket.objects.filter(user=self.student_user, event=self.event).exists())

    def test_successful_booking_ajax_returns_updated_count(self):
        """AJAX booking should respond with the updated registration metrics."""
        self.client.login(username='student@uog.com', password='password123')

        response = self.client.post(
            reverse('event_detail', args=[self.event.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['current_count'], 1)
        self.assertTrue(Ticket.objects.filter(user=self.student_user, event=self.event).exists())

    def test_login_accepts_phone_number(self):
        """Users should be able to sign in with the phone number advertised by the UI."""
        response = self.client.post(reverse('login'), {
            'account': '07111111111',
            'password': 'password123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

    def test_my_tickets_page_marks_future_ticket_as_upcoming_without_active_qr(self):
        """Future tickets should not show a live entry QR before the event starts."""
        Ticket.objects.create(user=self.student_user, event=self.event)
        self.client.login(username='student@uog.com', password='password123')

        response = self.client.get(reverse('my_tickets'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upcoming')
        self.assertContains(response, 'Available at Start Time')
        self.assertNotContains(response, 'data-qr-value=')

    def test_my_tickets_page_shows_qr_hook_for_live_ticket(self):
        """Live tickets should expose an active QR code during the event window."""
        live_event = Event.objects.create(
            society=self.society,
            title="Live Event",
            description="An event that is currently running.",
            location="Student Union",
            start_time=timezone.now() - timedelta(minutes=30),
            end_time=timezone.now() + timedelta(minutes=90),
            capacity=20
        )
        Ticket.objects.create(user=self.student_user, event=live_event)
        self.client.login(username='student@uog.com', password='password123')

        response = self.client.get(reverse('my_tickets'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-qr-value=')
        self.assertContains(response, 'Scan for Entry')

    def test_my_tickets_page_links_back_to_event_detail(self):
        """Each ticket should provide a direct route back to the event details page."""
        Ticket.objects.create(user=self.student_user, event=self.event)
        self.client.login(username='student@uog.com', password='password123')

        response = self.client.get(reverse('my_tickets'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('event_detail', args=[self.event.id]))

    def test_my_tickets_page_marks_past_event_ticket_as_expired(self):
        """Past-event tickets should display as expired even if the stored status is still valid."""
        past_event = Event.objects.create(
            society=self.society,
            title="Past Event",
            description="An event that already finished.",
            location="Old Hall",
            start_time=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=2) + timedelta(hours=2),
            capacity=10
        )
        Ticket.objects.create(user=self.student_user, event=past_event)
        self.client.login(username='student@uog.com', password='password123')

        response = self.client.get(reverse('my_tickets'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Expired')
        self.assertNotContains(response, 'Cancel Ticket')

    def test_expired_ticket_cannot_be_cancelled(self):
        """Ended-event tickets should remain in history even if a cancel POST is attempted."""
        past_event = Event.objects.create(
            society=self.society,
            title="Past Event",
            description="An event that already finished.",
            location="Old Hall",
            start_time=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=2) + timedelta(hours=2),
            capacity=10
        )
        ticket = Ticket.objects.create(user=self.student_user, event=past_event)
        self.client.login(username='student@uog.com', password='password123')

        response = self.client.post(reverse('cancel_ticket', args=[ticket.id]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Ticket.objects.filter(pk=ticket.pk).exists())

    def test_event_detail_page_shows_share_action(self):
        """The event detail page should expose a share action for the current event."""
        self.client.login(username='student@uog.com', password='password123')

        response = self.client.get(reverse('event_detail', args=[self.event.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Share Event')

    def test_admin_event_detail_shows_check_in_tools(self):
        """Organisers should see attendee check-in controls on their event page."""
        Ticket.objects.create(user=self.student_user, event=self.event)
        self.client.login(username='admin@uog.com', password='password123')

        response = self.client.get(reverse('event_detail', args=[self.event.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Check-in Desk')
        self.assertContains(response, 'Scan QR')

    def test_admin_can_check_in_ticket_by_reference_code(self):
        """An organiser should be able to mark an attendee ticket as used."""
        self.event.start_time = timezone.now() - timedelta(minutes=30)
        self.event.end_time = timezone.now() + timedelta(minutes=90)
        self.event.save(update_fields=['start_time', 'end_time'])
        ticket = Ticket.objects.create(user=self.student_user, event=self.event)
        self.client.login(username='admin@uog.com', password='password123')

        response = self.client.post(
            reverse('check_in_ticket', args=[self.event.id]),
            {'ticket_code': ticket.ticket_code},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'used')

    def test_admin_cannot_check_in_ticket_before_event_starts(self):
        """Organisers should not be able to check attendees in before the event begins."""
        ticket = Ticket.objects.create(user=self.student_user, event=self.event)
        self.client.login(username='admin@uog.com', password='password123')

        response = self.client.post(
            reverse('check_in_ticket', args=[self.event.id]),
            {'ticket_code': ticket.ticket_code},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 400)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'valid')

    def test_student_cannot_check_in_ticket_for_event(self):
        """Non-organisers should not be allowed to use the attendee check-in endpoint."""
        ticket = Ticket.objects.create(user=self.student_user, event=self.event)
        self.client.login(username='student@uog.com', password='password123')

        response = self.client.post(
            reverse('check_in_ticket', args=[self.event.id]),
            {'ticket_code': ticket.ticket_code},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 403)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'valid')

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

    def test_event_form_preserves_full_end_datetime(self):
        """The event form should keep the submitted end date instead of collapsing it to the start date."""
        form = EventForm(data={
            'title': 'Conference',
            'description': 'Two-day event',
            'location': 'Main Hall',
            'start_time': '2026-03-25T18:00',
            'end_time': '2026-03-26T09:30',
            'capacity': 50,
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['end_time'].date().isoformat(), '2026-03-26')

    def test_event_form_rejects_zero_capacity(self):
        """Event capacity should stay positive to avoid invalid registration states."""
        form = EventForm(data={
            'title': 'Conference',
            'description': 'Zero-capacity event',
            'location': 'Main Hall',
            'start_time': '2026-03-25T18:00',
            'end_time': '2026-03-25T19:30',
            'capacity': 0,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('capacity', form.errors)

    def test_admin_dashboard_bootstraps_missing_society_description(self):
        """First-time admins should receive a valid society record instead of crashing."""
        bootstrap_admin = User.objects.create_user(
            username='bootstrap@uog.com',
            email='bootstrap@uog.com',
            password='password123',
            role=User.SOCIETY_ADMIN,
            phone_number='07333333333'
        )
        self.client.login(username='bootstrap@uog.com', password='password123')

        response = self.client.get(reverse('admin_dashboard'))

        self.assertEqual(response.status_code, 200)
        bootstrap_admin.refresh_from_db()
        self.assertTrue(Society.objects.filter(admin=bootstrap_admin, description='Society profile pending update.').exists())

    def test_account_settings_updates_phone_number(self):
        """Users should be able to update their stored phone number."""
        self.client.login(username='student@uog.com', password='password123')

        response = self.client.post(reverse('account_settings'), {
            'form_type': 'phone',
            'phone_number': '07999999999',
        })

        self.assertEqual(response.status_code, 302)
        self.student_user.refresh_from_db()
        self.assertEqual(self.student_user.phone_number, '07999999999')

    def test_account_settings_updates_password_and_keeps_session(self):
        """Changing a password should keep the user signed in and accept the new password."""
        self.client.login(username='student@uog.com', password='password123')

        response = self.client.post(reverse('account_settings'), {
            'form_type': 'password',
            'old_password': 'password123',
            'new_password1': 'updatedPass456!',
            'new_password2': 'updatedPass456!',
        })

        self.assertEqual(response.status_code, 302)

        follow_up = self.client.get(reverse('account_settings'))
        self.assertEqual(follow_up.status_code, 200)

        self.client.logout()
        self.assertTrue(self.client.login(username='student@uog.com', password='updatedPass456!'))

    def test_account_settings_deletes_account_with_current_password(self):
        """Deleting an account should remove the user record and redirect out of the app."""
        self.client.login(username='student@uog.com', password='password123')

        response = self.client.post(reverse('account_settings'), {
            'form_type': 'delete_account',
            'current_password': 'password123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('landing'))
        self.assertFalse(User.objects.filter(pk=self.student_user.pk).exists())

    def test_admin_can_create_event(self):
        """Society admins should be able to create a new event."""
        self.client.login(username='admin@uog.com', password='password123')

        response = self.client.post(reverse('create_event'), {
            'title': 'Freshers Fair',
            'description': 'Welcome event for new members.',
            'location': 'Atrium',
            'start_time': '2026-04-10T18:00',
            'end_time': '2026-04-10T20:00',
            'capacity': 120,
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Event.objects.filter(title='Freshers Fair', society=self.society).exists())

    def test_admin_can_edit_owned_event(self):
        """Society admins should be able to edit their own event."""
        self.client.login(username='admin@uog.com', password='password123')

        response = self.client.post(reverse('edit_event', args=[self.event.id]), {
            'title': 'Updated Workshop',
            'description': 'Updated description.',
            'location': 'Library Room 2',
            'start_time': '2026-04-10T18:00',
            'end_time': '2026-04-10T20:00',
            'capacity': 80,
        })

        self.assertEqual(response.status_code, 302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, 'Updated Workshop')
        self.assertEqual(self.event.location, 'Library Room 2')

    def test_non_owner_cannot_edit_event(self):
        """Students should be blocked from editing admin-owned events."""
        self.client.login(username='student@uog.com', password='password123')

        response = self.client.get(reverse('edit_event', args=[self.event.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin_dashboard'))

    def test_admin_can_delete_owned_event(self):
        """Deleting an event should remove it from the database."""
        self.client.login(username='admin@uog.com', password='password123')

        response = self.client.post(reverse('delete_event', args=[self.event.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Event.objects.filter(pk=self.event.pk).exists())

    def test_population_script_creates_demo_dataset(self):
        """The standalone population script should build a useful demo dataset."""
        from population_script import populate

        populate()

        self.assertGreaterEqual(Event.objects.count(), 6)
        self.assertGreaterEqual(Ticket.objects.count(), 8)
        self.assertTrue(User.objects.filter(role=User.SOCIETY_ADMIN, email='tech_admin@uog.com').exists())
        self.assertTrue(User.objects.filter(role=User.STUDENT, email='amy.student@uog.com').exists())
