import os
# Configure the project settings environment for the standalone script
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'society_ticket_manager.settings')

import django
django.setup()

from events.models import Event, Society, User
from django.utils import timezone
from datetime import datetime, timedelta

def create_user(username, first_name):
    """Helper to create a unique society admin."""
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': username,
            'role': User.SOCIETY_ADMIN,
            'first_name': first_name
        }
    )
    if created:
        user.set_password('password123')
        user.save()
    return user

def populate():
    """
    Populates the database with fresh data.
    Each society is assigned a UNIQUE admin to avoid constraint errors.
    """
    # 0. Clean old data to ensure a fresh demo dataset
    print("Clearing old data...")
    Event.objects.all().delete()
    Society.objects.all().delete()
    # Note: We keep users but the script handles them via get_or_create

    # 1. Create Unique Admins for each Society
    admin_tech = create_user('tech_admin@uog.com', 'Tech Manager')
    admin_music = create_user('music_admin@uog.com', 'Arts Manager')
    admin_food = create_user('food_admin@uog.com', 'Cultural Manager')

    # 2. Get or Create Societies with their UNIQUE admins
    tech_soc, _ = Society.objects.get_or_create(
        name="Computer Science Society",
        defaults={'admin': admin_tech, 'description': 'Organises technical workshops.'},
    )
    music_soc, _ = Society.objects.get_or_create(
        name="Music & Arts Society",
        defaults={'admin': admin_music, 'description': 'Hosts performances and creative showcases.'},
    )
    food_soc, _ = Society.objects.get_or_create(
        name="Culinary & Cultural Society",
        defaults={'admin': admin_food, 'description': 'Brings together food and culture.'},
    )

    # 3. Define the sample events
    events_data = [
        {
            "soc": food_soc,
            "title": "Global Food Festival 2026",
            "description": "Experience flavors from over 20 countries. Free entry!",
            "location": "Student Union Plaza",
            "capacity": 300,
            "start_time": timezone.make_aware(datetime(2026, 6, 15, 12, 0, 0)),
            "image": "event_images/unnamed.jpg"
        },
        {
            "soc": tech_soc,
            "title": "Python Workshop 2026",
            "description": "Learn practical Python skills through hands-on exercises.",
            "location": "Main Campus, Building A",
            "capacity": 50,
            "start_time": timezone.now() + timedelta(days=14),
            "image": "event_images/微信图片_20260306230917.png"
        },
        {
            "soc": music_soc,
            "title": "Campus Music Fest 2026",
            "description": "Live performances from student bands.",
            "location": "West Campus Lawn",
            "capacity": 200,
            "start_time": timezone.now() + timedelta(days=21),
            "image": "event_images/74be05470c2f3f0679093562513d0e6.png"
        }
    ]

    # 4. Iterate and create events
    for data in events_data:
        # Using get_or_create for events to avoid duplicates if run multiple times
        event, created = Event.objects.get_or_create(
            title=data['title'],
            defaults={
                'society': data['soc'],
                'description': data['description'],
                'location': data['location'],
                'capacity': data['capacity'],
                'start_time': data['start_time'],
                'end_time': data['start_time'] + timedelta(hours=3),
                'image': data['image']
            }
        )
        if created:
            print(f"- Created Event: {data['title']}")
        else:
            print(f"- Event already exists: {data['title']}")

if __name__ == '__main__':
    print("Starting population script...")
    try:
        populate()
        print("Success: Database is now populated[cite: 96].")
    except Exception as e:
        print(f"An error occurred: {e}")