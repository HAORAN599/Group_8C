import os
# Configure the project settings environment for the standalone script
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'society_ticket_manager.settings')

import django
django.setup()

from events.models import Event, Society, User
from django.utils import timezone
from datetime import datetime, timedelta

def populate():
    """
    Populates the database with four high-quality events:
    1. Global Food Festival (Precise Date)
    2. Python AI Workshop
    3. Campus Music Fest
    4. Midnight Stargazing & Cinema (Creative Event)
    """
    # 0. Clean old data to ensure a fresh, professional showcase
    print("Clearing old event data...")
    Event.objects.all().delete()

    # 1. Get or Create Admin User
    admin_username = 'admin@uog.com'
    user, created = User.objects.get_or_create(
        username=admin_username,
        defaults={
            'email': admin_username,
            'role': 2, # Society Admin role
            'first_name': 'Global Admin'
        }
    )
    if created:
        user.set_password('password123')
        user.save()

    # 2. Get or Create Societies for a realistic variety
    tech_soc, _ = Society.objects.get_or_create(name="Computer Science Society", defaults={'admin': user})
    music_soc, _ = Society.objects.get_or_create(name="Music & Arts Society", defaults={'admin': user})
    food_soc, _ = Society.objects.get_or_create(name="Culinary & Cultural Society", defaults={'admin': user})

    # 3. Define the full set of creative and standard events
    # Images are mapped to your specific file names
    events_data = [
        {
            "soc": food_soc,
            "title": "Global Food Festival 2026",
            "description": "Experience flavors from over 20 countries right on our campus. Free entry for all students!",
            "location": "Student Union Plaza & Lawn",
            "capacity": 300,
            "start_time": timezone.make_aware(datetime(2026, 6, 15, 12, 0, 0)),
            "image": "event_images/unnamed.jpg" 
        },
        {
            "soc": tech_soc,
            "title": "Python AI Workshop 2026",
            "description": "Learn the basics of Neural Networks with hands-on practice using TensorFlow.",
            "location": "Main Campus, Building A",
            "capacity": 50,
            "start_time": timezone.now() + timedelta(days=14),
            "image": "event_images/微信图片_20260306230917.png"
        },
        {
            "soc": music_soc,
            "title": "Campus Music Fest 2026",
            "description": "A night of live performances from our student bands under the stars.",
            "location": "West Campus Central Lawn",
            "capacity": 200,
            "start_time": timezone.now() + timedelta(days=21),
            "image": "event_images/74be05470c2f3f0679093562513d0e6.png"
        },
        {
            "soc": music_soc,
            "title": "Midnight Stargazing & Open-Air Cinema",
            "description": "A magical night featuring a 4K screening of 'Interstellar' and telescope stargazing sessions.",
            "location": "University Observatory Garden",
            "capacity": 80,
            "start_time": timezone.now() + timedelta(days=7),
            "image": "event_images/stargazing.jpg" 
        }
    ]

    # 4. Iterate and create events in the database
    for data in events_data:
        Event.objects.create(
            society=data['soc'],
            title=data['title'],
            description=data['description'],
            location=data['location'],
            capacity=data['capacity'],
            start_time=data['start_time'],
            end_time=data['start_time'] + timedelta(hours=3),
            image=data['image']
        )
        print(f"- Added Event: {data['title']}")

if __name__ == '__main__':
    print("Starting final 'Super Showcase' population script...")
    try:
        populate()
        print("Success: Your professional campus platform is now live with 4 diverse events!")
    except Exception as e:
        print(f"An error occurred during population: {e}")