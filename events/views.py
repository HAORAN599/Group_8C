from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import User, Event, Society, Ticket, Review
from .forms import EventForm

def login_view(request):
    selected_role = request.GET.get('role', 'student')
    if request.method == 'POST':
        account = request.POST.get('account')
        password = request.POST.get('password')
        user = User.objects.filter(Q(email=account) | Q(phone_number=account)).first()

        if user and user.check_password(password):


            if selected_role == 'society_admin' and user.role != User.SOCIETY_ADMIN and not user.is_superuser:
                return render(request, 'events/login.html', {
                    'error': 'This account does not have admin privileges.',
                    'current_role': selected_role
                })


            login(request, user)


            if selected_role == 'society_admin':
                return redirect('admin_dashboard')
            else:
                return redirect('home')

        else:
            return render(request, 'events/login.html', {
                'error': 'Account or password incorrect.',
                'current_role': selected_role
            })

    return render(request, 'events/login.html', {'current_role': selected_role})

def register_view(request):
    selected_role = request.GET.get('role', 'student')
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        context = {'current_role': selected_role}
        if len(password) < 8:
            context['error'] = 'at least 8 letters'
            return render(request, 'events/register.html', context)
        if password != confirm_password:
            context['error'] = 'two times entered incorrect'
            return render(request, 'events/register.html', context)
        if User.objects.filter(email=email).exists():
            context['error'] = 'this email have been registered'
            return render(request, 'events/register.html', context)

        if User.objects.filter(phone_number=phone).exists():
            context['error'] = 'this phone number has been registered'
            return render(request, 'events/register.html', context)
        db_role = User.STUDENT if selected_role == 'student' else User.SOCIETY_ADMIN
        user = User.objects.create_user(username=email, email=email, password=password, role=db_role, phone_number=phone)
        user.first_name = name
        user.save()
        login(request, user)
        return redirect('home') if db_role == User.STUDENT else redirect('admin_dashboard')
    return render(request, 'events/register.html', {'current_role': selected_role})

def landing_page(request):
    return render(request, 'events/landing.html')

@login_required
def home(request):
    query = request.GET.get('q')
    if query:
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
    event = get_object_or_404(Event, id=event_id)
    already_has_ticket = Ticket.objects.filter(user=request.user, event=event).exists()
    if request.method == 'POST' and not already_has_ticket:
        if event.tickets.count() < event.capacity:
            Ticket.objects.create(user=request.user, event=event)
            return redirect('my_tickets')
    return render(request, 'events/event_detail.html', {
        'event': event, 
        'already_has_ticket': already_has_ticket
    })

@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, 'events/my_tickets.html', {'tickets': tickets})

@login_required
def admin_dashboard(request):
    if request.user.role != User.SOCIETY_ADMIN and not request.user.is_superuser:
        return redirect('home')
    society, created = Society.objects.get_or_create(
        admin=request.user, 
        defaults={'name': f"{request.user.first_name}'s Society"}
    )
    events = society.events.all()
    return render(request, 'events/admin_dashboard.html', {'society': society, 'events': events})

def logout_view(request):
    logout(request)
    return redirect('landing')


def cancel_ticket(request, ticket_id):
    #  get_object_or_404 and limit user=request.user，make sure can only delete own ticket
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)

    if request.method == 'POST':
        ticket.delete()
        return redirect('my_tickets')

    return redirect('my_tickets')


@login_required
def create_event(request):

    if request.user.role != User.SOCIETY_ADMIN and not request.user.is_superuser:
        return redirect('home')


    society, created = Society.objects.get_or_create(
        admin=request.user,
        defaults={'name': f"{request.user.first_name}'s Society"}
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
    event = get_object_or_404(Event, id=event_id)


    if request.user != event.society.admin and not request.user.is_superuser:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        event.delete()

    return redirect('admin_dashboard')
