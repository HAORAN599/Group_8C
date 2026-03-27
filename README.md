# University Society Event & Ticketing Manager

## Project Overview

This Django web app helps university societies create and manage events, while giving students an easy way to discover what is happening on campus and book tickets.

- Live Demo: [https://haoranwei.pythonanywhere.com/](https://haoranwei.pythonanywhere.com/)
- GitHub Repository: [https://github.com/HAORAN599/Group_8C](https://github.com/HAORAN599/Group_8C)

---

## Key Features

### Administrator Features

- Event Management (CRUD): Society admins can create, edit, and remove events from one place.
- Ticketing Control: Each event can have a booking limit, so registrations stop once it is full.

### Student & User Features

- Event Discovery: Students can quickly search for events by keyword and browse what is coming up.
- Map Integration: Each booking page includes a map so users can easily find the venue.
- Email Notifications: After booking, users receive a confirmation email with their booking details, venue, and ticket information.
- My Tickets: Students can view all of their bookings in one place and cancel them if their plans change.

### Account Management

- Profile Customization: Users can update their details whenever they need to.
- Account Deletion: Users can delete their account if they no longer want to use the system.

---

## 🛠️ Technology Stack

- Backend: Django with Python 3.11
- Environment Management: `venv` for managing the local development environment
- Mapping: Google Maps Embed for showing event locations
- Emailing: Django SMTP backend for booking confirmation emails

---

## 🚀 Local Setup Guide

To run the project locally:

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install the required packages.
4. Run the migrations and add the sample data.
5. Start the development server.

```bash
git clone https://github.com/HAORAN599/Group_8C.git
cd Group_8C
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python population_script.py
python manage.py runserver
```

To run the test suite, use `python manage.py test`.

The project can be set up on another machine by installing the packages from `requirements.txt`, running the migrations, and then using `population_script.py` to add sample data.

---

## 📌 External Sources

This project uses Bootstrap 5, Bootstrap Icons, jQuery, QRCode.js, and Google Maps Embed to handle styling, interactivity, QR code generation, and location display.
