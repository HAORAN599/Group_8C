# University Society Event & Ticketing Manager

##  Project Overview
This is a Django-based web application designed for university societies to manage event publishing and ticket bookings. The system empowers society administrators to handle logistics while providing students with a seamless experience to discover and join events.


* **Live Demo**: [https://haoranwei.pythonanywhere.com/](https://haoranwei.pythonanywhere.com/)

---

##  Key Features

### Administrator Features
* **Event Management (CRUD)**: Create, edit, and delete society events with ease.
* **Ticketing Control**: Set available ticket quotas and enforce maximum capacity limits for every event.

### Student & User Features
* **Event Discovery**: Integrated search functionality to find specific events quickly.
* **Map Integration**: View exact event locations via an interactive map on the booking page.
* **Email Notifications**: Receive automated confirmation emails upon booking, including **Booking ID**, **Venue**, and event details.
* **My Tickets**: A dedicated dashboard to view all booked events and perform bulk cancellations if plans change.

### Account Management
* **Profile Customization**: Users can update their personal information at any time.
* **Account Deletion**: Users have the autonomy to close and delete their accounts if they are no longer needed.

---

## 🛠️ Technology Stack
* **Backend**: Django (Python 3.11)
* **Environment Management**: `venv` (Virtual Environment)
* **Mapping**: (e.g., Google Maps API / Leaflet - *update if applicable*)
* **Emailing**: Django SMTP Backend

---

## 🚀 Local Setup Guide

### 1. Clone the Repository
```bash
git clone https://github.com/HAORAN599/Group_8C.git
```

### 2. Configure Virtual Environment
```bash
# Create the virtual environment
python -m venv venv

# Activate the environment (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```
### 3. Database Initialization
```bash
python manage.py makemigrations
python manage.py migrate

# Populate the database with initial society and event data
python population_script.py
```
### 4. Run the Development Server
```bash
python manage.py runserver
```