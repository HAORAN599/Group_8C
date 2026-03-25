from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import User, Event, Society, Ticket, Review
from .forms import EventForm, AccountPhoneForm, StyledPasswordChangeForm
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings

# --- Authentication Views ---

def login_view(request):
    """
    Handles user login for both Students and Society Admins.
    Uses email as the sign-in identifier.
    """
    selected_role = request.GET.get('role', 'student')
    if request.method == 'POST':
        email = request.POST.get('account', '').strip().lower()
        password = request.POST.get('password')
        user = User.objects.filter(email=email).first()

        if user and user.check_password(password):
            # Role-based access control: check if the user has the required role
            if selected_role == 'society_admin' and user.role != User.SOCIETY_ADMIN and not user.is_superuser:
                return render(request, 'events/login.html', {
                    'error': 'This account does not have admin privileges.',
                    'current_role': selected_role
                })

            login(request, user)

            # Redirect based on user role after successful login
            if selected_role == 'society_admin':
                return redirect('admin_dashboard')
            else:
                return redirect('home')

        else:
            return render(request, 'events/login.html', {
                'error': 'Email or password incorrect.',
                'current_role': selected_role
            })

    return render(request, 'events/login.html', {'current_role': selected_role})


def register_view(request):
    selected_role = request.GET.get('role', 'student')
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        context = {'current_role': selected_role}

        # check does the password the same
        if password != confirm_password:
            context['error'] = 'Passwords do not match.'
            return render(request, 'events/register.html', context)

        existing_email_user = User.objects.filter(email=email).first()
        existing_phone_user = User.objects.filter(phone_number=phone).exclude(email=email).first() if phone else None

        if existing_email_user:

            if selected_role == 'society_admin' and existing_email_user.role == User.STUDENT:

                if existing_email_user.check_password(password):
                    existing_email_user.role = User.SOCIETY_ADMIN
                    existing_email_user.first_name = name
                    existing_email_user.phone_number = phone
                    existing_email_user.save()

                    login(request, existing_email_user)
                    return redirect('admin_dashboard')
                else:

                    context[
                        'error'] = 'This email is already registered as a student. Please enter the correct password to upgrade to Admin.'
                    return render(request, 'events/register.html', context)


            else:
                context['error'] = 'This email address is already registered.'
                return render(request, 'events/register.html', context)

        if existing_phone_user:
                context['error'] = 'This phone number is already attached to another account.'
                return render(request, 'events/register.html', context)

        # for new
        db_role = User.STUDENT if selected_role == 'student' else User.SOCIETY_ADMIN
        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                role=db_role,
                phone_number=phone
            )
            user.first_name = name
            user.save()

            login(request, user)
            return redirect('home') if db_role == User.STUDENT else redirect('admin_dashboard')
        except Exception as e:
            context['error'] = f'Registration failed: {str(e)}'
            return render(request, 'events/register.html', context)

    return render(request, 'events/register.html', {'current_role': selected_role})

def landing_page(request):
    """Entry point of the application."""
    return render(request, 'events/landing.html')

# --- Student Views ---

@login_required
def home(request):
    """
    Displays the event list with a search feature filtering by 
    title, description, location, or society name.
    """
    query = request.GET.get('q')
    if query:
        # Complex filtering using Q objects for a better user search experience
        events = Event.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) | 
            Q(location__icontains=query) |
            Q(society__name__icontains=query)
        ).distinct().order_by('start_time')
    else:
        events = Event.objects.all().order_by('start_time')
    return render(request, 'events/home.html', {'events': events, 'query': query})


@login_required
def event_detail(request, event_id):
    """
    Displays detailed information for a specific event and handles ticket booking.
    Includes capacity check to prevent overselling, and sends a confirmation email.
    """
    event = get_object_or_404(Event, id=event_id)
    is_organizer = request.user == event.society.admin
    user_ticket = Ticket.objects.filter(user=request.user, event=event).first()
    already_has_ticket = user_ticket is not None

    if request.method == 'POST' and not already_has_ticket and not is_organizer:
        # Validate capacity before ticket creation
        if event.tickets.count() < event.capacity:

            ticket = Ticket.objects.create(user=request.user, event=event)


            subject = f"Booking Confirmation: {event.title}"
            message = f"""
            Hi {request.user.first_name},

            You have successfully booked a ticket for '{event.title}'.

            Here are your event details:
            - Location: {event.location}
            - Start Time: {event.start_time.strftime('%Y-%m-%d %H:%M')}
            - Your Ticket Code: {ticket.ticket_code}

            Looking forward to seeing you there!
            """


            try:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [request.user.email],
                    fail_silently=False,
                )
            except Exception as e:

                print(f"Error sending email: {e}")


            return redirect('my_tickets')

    return render(request, 'events/event_detail.html', {
        'event': event,
        'already_has_ticket': already_has_ticket,
        'is_organizer': is_organizer,
        'user_ticket': user_ticket,
    })

@login_required
def my_tickets(request):
    """Lists all tickets purchased by the current logged-in student."""
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, 'events/my_tickets.html', {'tickets': tickets})


@login_required
def account_settings(request):
    """Allows users to manage account details without leaving the app flow."""
    phone_form = AccountPhoneForm(instance=request.user)
    password_form = StyledPasswordChangeForm(user=request.user)
    is_admin_user = request.user.role == User.SOCIETY_ADMIN or request.user.is_superuser

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'phone':
            phone_form = AccountPhoneForm(request.POST, instance=request.user)
            if phone_form.is_valid():
                phone_form.save()
                messages.success(request, 'Phone number updated successfully.')
                return redirect('account_settings')
        elif form_type == 'password':
            password_form = StyledPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password updated successfully.')
                return redirect('account_settings')
        else:
            messages.error(request, 'Please submit a valid settings form.')
            return redirect('account_settings')

    return render(request, 'events/account_settings.html', {
        'phone_form': phone_form,
        'password_form': password_form,
        'is_admin_user': is_admin_user,
    })

@login_required
def cancel_ticket(request, ticket_id):
    """
    Allows students to cancel their bookings. 
    Secured to ensure users can only delete their own tickets.
    """
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    if request.method == 'POST':
        ticket.delete()
    return redirect('my_tickets')

# --- Admin Views ---

@login_required
def admin_dashboard(request):
    """
    Main dashboard for Society Admins to manage their events.
    Redirects non-admin users to the home page for security.
    """
    if request.user.role != User.SOCIETY_ADMIN and not request.user.is_superuser:
        return redirect('home')
    
    # Ensure every admin has an associated Society object
    society, created = Society.objects.get_or_create(
        admin=request.user, 
        defaults={'name': f"Society of {request.user.first_name} (ID:{request.user.id})"}
    )
    events = society.events.all()
    total_registrations = Ticket.objects.filter(event__in=events).count()
    return render(request, 'events/admin_dashboard.html', {
        'society': society,
        'events': events,
        'total_registrations': total_registrations,
    })

@login_required
def create_event(request):
    """Handles the creation of new events via a Django ModelForm."""
    if request.user.role != User.SOCIETY_ADMIN and not request.user.is_superuser:
        return redirect('home')

    society, created = Society.objects.get_or_create(
        admin=request.user,
        defaults={'name': f"Society of {request.user.first_name} (ID:{request.user.id})"}
    )

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.society = society
            event.save()
            return redirect('admin_dashboard')
    else:
        form = EventForm()

    return render(request, 'events/create_event.html', {'form': form})

@login_required
def delete_event(request, event_id):
    """
    Allows admins to delete events. 
    Checks if the user is the owner of the event for security purposes.
    """
    event = get_object_or_404(Event, id=event_id)
    if request.user != event.society.admin and not request.user.is_superuser:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        event.delete()
    return redirect('admin_dashboard')

def logout_view(request):
    """Logs out the user and redirects to the landing page."""
    logout(request)
    return redirect('landing')


@login_required
def edit_event(request, event_id):

    event = get_object_or_404(Event, id=event_id)


    if request.user != event.society.admin and not request.user.is_superuser:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:

        form = EventForm(instance=event)

    return render(request, 'events/edit_event.html', {'form': form, 'event': event})
