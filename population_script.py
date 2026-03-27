import os
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'society_ticket_manager.settings')

import django
django.setup()

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from events.models import Event, Review, Society, Ticket, User


DEFAULT_PASSWORD = 'password123'


def create_user(username, first_name, role, phone_number=None):
    """Create or update a predictable demo account."""
    filters = Q(username=username) | Q(email=username)
    if phone_number:
        filters |= Q(phone_number=phone_number)

    user = User.objects.filter(filters).first()
    created = user is None
    if created:
        user = User(username=username)

    user.email = username
    user.username = username
    user.role = role
    user.first_name = first_name
    user.phone_number = phone_number
    user.set_password(DEFAULT_PASSWORD)
    if created:
        user.save()
    else:
        user.save(update_fields=['email', 'role', 'first_name', 'phone_number', 'password'])
    return user


def populate():
    """Create a fresh demo dataset that is useful for marking and local testing."""
    with transaction.atomic():
        print('Clearing old demo data...')
        Review.objects.all().delete()
        Ticket.objects.all().delete()
        Event.objects.all().delete()
        Society.objects.all().delete()

        admin_tech = create_user('tech_admin@uog.com', 'Tech Manager', User.SOCIETY_ADMIN)
        admin_music = create_user('music_admin@uog.com', 'Arts Manager', User.SOCIETY_ADMIN)
        admin_food = create_user('food_admin@uog.com', 'Culture Manager', User.SOCIETY_ADMIN)

        student_amy = create_user('amy.student@uog.com', 'Amy', User.STUDENT, '07111111111')
        student_ben = create_user('ben.student@uog.com', 'Ben', User.STUDENT, '07222222222')
        student_cara = create_user('cara.student@uog.com', 'Cara', User.STUDENT, '07333333333')

        tech_soc = Society.objects.create(
            name='Computer Science Society',
            description='Runs technical workshops, coding socials, and hack sessions.',
            admin=admin_tech,
        )
        music_soc = Society.objects.create(
            name='Music & Arts Society',
            description='Hosts performances, jam nights, and creative showcases.',
            admin=admin_music,
        )
        food_soc = Society.objects.create(
            name='Culinary & Cultural Society',
            description='Brings together food, culture, and community events.',
            admin=admin_food,
        )

        now = timezone.now()
        event_specs = [
            {
                'society': tech_soc,
                'title': 'Python Workshop',
                'description': 'A practical coding session covering APIs, testing, and deployment tips.',
                'location': 'Main Campus, Building A',
                'capacity': 40,
                'start_time': now + timedelta(days=5, hours=2),
                'duration_hours': 2,
            },
            {
                'society': tech_soc,
                'title': 'Hack Night Live',
                'description': 'A collaborative coding event with live check-in and mentoring.',
                'location': 'Innovation Lab',
                'capacity': 25,
                'start_time': now - timedelta(minutes=30),
                'duration_hours': 3,
            },
            {
                'society': music_soc,
                'title': 'Campus Music Fest',
                'description': 'An evening of student bands, acoustic sets, and collaborative performances.',
                'location': 'West Campus Lawn',
                'capacity': 150,
                'start_time': now + timedelta(days=12),
                'duration_hours': 4,
            },
            {
                'society': food_soc,
                'title': 'Global Food Festival',
                'description': 'Tastings, cultural showcases, and society stalls across the student plaza.',
                'location': 'Student Union Plaza',
                'capacity': 220,
                'start_time': now + timedelta(days=18, hours=3),
                'duration_hours': 5,
            },
            {
                'society': food_soc,
                'title': 'Street Food Night',
                'description': 'A smaller evening market already at capacity for booking-limit testing.',
                'location': 'Riverside Courtyard',
                'capacity': 3,
                'start_time': now + timedelta(days=2, hours=5),
                'duration_hours': 3,
            },
            {
                'society': music_soc,
                'title': 'Winter Showcase Archive',
                'description': 'A completed event kept in the dataset to demonstrate ticket history and reviews.',
                'location': 'The Great Hall',
                'capacity': 90,
                'start_time': now - timedelta(days=10),
                'duration_hours': 2,
            },
        ]

        events = {}
        for spec in event_specs:
            event = Event.objects.create(
                society=spec['society'],
                title=spec['title'],
                description=spec['description'],
                location=spec['location'],
                capacity=spec['capacity'],
                start_time=spec['start_time'],
                end_time=spec['start_time'] + timedelta(hours=spec['duration_hours']),
            )
            events[event.title] = event
            print(f'- Created event: {event.title}')

        Ticket.objects.create(user=student_amy, event=events['Python Workshop'])
        Ticket.objects.create(user=student_ben, event=events['Hack Night Live'])
        Ticket.objects.create(user=student_cara, event=events['Hack Night Live'], status='used')
        Ticket.objects.create(user=student_amy, event=events['Campus Music Fest'])
        Ticket.objects.create(user=student_ben, event=events['Global Food Festival'])
        Ticket.objects.create(user=student_amy, event=events['Street Food Night'])
        Ticket.objects.create(user=student_ben, event=events['Street Food Night'])
        Ticket.objects.create(user=student_cara, event=events['Street Food Night'])
        Ticket.objects.create(user=student_cara, event=events['Winter Showcase Archive'], status='used')

        Review.objects.create(
            event=events['Winter Showcase Archive'],
            user=student_amy,
            rating=5,
            comment='Well organised event with a smooth ticketing experience.',
        )
        Review.objects.create(
            event=events['Winter Showcase Archive'],
            user=student_ben,
            rating=4,
            comment='Great atmosphere and clear event information.',
        )

        print('\nDemo accounts created:')
        print(f'- Society admin: tech_admin@uog.com / {DEFAULT_PASSWORD}')
        print(f'- Society admin: music_admin@uog.com / {DEFAULT_PASSWORD}')
        print(f'- Society admin: food_admin@uog.com / {DEFAULT_PASSWORD}')
        print(f'- Student: amy.student@uog.com / {DEFAULT_PASSWORD}')
        print(f'- Student: ben.student@uog.com / {DEFAULT_PASSWORD}')
        print(f'- Student: cara.student@uog.com / {DEFAULT_PASSWORD}')


if __name__ == '__main__':
    print('Starting population script...')
    try:
        populate()
        print('Success: database is now populated.')
    except Exception as error:
        print(f'An error occurred: {error}')
