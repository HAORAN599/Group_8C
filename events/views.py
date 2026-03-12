from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import User, Event, Society, Ticket, Review

def login_view(request):
    selected_role = request.GET.get('role', 'student')
    if request.method == 'POST':
        account = request.POST.get('account')
        password = request.POST.get('password')
        user = User.objects.filter(Q(email=account) | Q(phone_number=account)).first()
        if user and user.check_password(password):
            login(request, user)
            return redirect('home') if user.role == User.STUDENT else redirect('admin_dashboard')
        else:
            return render(request, 'events/login.html', {
                'error': 'account or password incorrect',
                'current_role': selected_role
            })
    return render(request, 'events/login.html', {'current_role': selected_role})

def register_view(request):
    selected_role = request.GET.get('role', 'student')
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
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
        db_role = User.STUDENT if selected_role == 'student' else User.SOCIETY_ADMIN
        user = User.objects.create_user(username=email, email=email, password=password, role=db_role)
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
    if request.user.role != User.SOCIETY_ADMIN:
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
