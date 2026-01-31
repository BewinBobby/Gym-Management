from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect
from django.http import Http404
from django.contrib.auth.models import User
from django.contrib import messages, auth
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from memberships.forms import MembershipChoiceForm, TrainerChoiceForm
from memberships.models import Appointment, Membership, Trainee, Trainer, DietPlan, WorkoutPlan
# Create your views here.

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about_us.html')

def contact(request):
    return render(request, 'contact.html')

def services(request):
    return render(request, 'services.html')

def get_available_trainers(slot_dt):
    """
    Return trainers who don't have a non-cancelled appointment at the given datetime.
    """
    conflicting = Appointment.objects.filter(
        appointment_date=slot_dt
    ).exclude(status='Cancelled')

    busy_ids = conflicting.values_list('trainer_id', flat=True)
    return Trainer.objects.exclude(id__in=busy_ids)


def is_trainer_available(trainer, slot_dt):
    """
    Check if a trainer is free at given datetime.
    """
    return not Appointment.objects.filter(
        trainer=trainer,
        appointment_date=slot_dt
    ).exclude(status='Cancelled').exists()

@login_required
def trainer_dashboard(request):
    # 1. Get the Trainer object for this logged-in user
    trainer = get_object_or_404(Trainer, user=request.user)

    # 2. Handle POST actions (add plans, adjust appointments)
    if request.method == "POST":
        # A. Add Diet Plan
        if 'add_diet_plan' in request.POST:
            trainee_id = request.POST.get('trainee_id')
            plan_details = request.POST.get('plan_details')

            trainee = get_object_or_404(Trainee, id=trainee_id)
            if plan_details.strip():
                DietPlan.objects.create(
                    trainee=trainee,
                    plan_details=plan_details.strip()
                )
                messages.success(request, f"Diet plan added for {trainee.user.get_full_name() or trainee.user.username}.")
            else:
                messages.error(request, "Diet plan details cannot be empty.")

            return redirect('trainer_dashboard')

        # B. Add Workout Plan
        if 'add_workout_plan' in request.POST:
            trainee_id = request.POST.get('trainee_id')
            plan_details = request.POST.get('plan_details')

            trainee = get_object_or_404(Trainee, id=trainee_id)
            if plan_details.strip():
                WorkoutPlan.objects.create(
                    trainee=trainee,
                    plan_details=plan_details.strip()
                )
                messages.success(request, f"Workout plan added for {trainee.user.get_full_name() or trainee.user.username}.")
            else:
                messages.error(request, "Workout plan details cannot be empty.")

            return redirect('trainer_dashboard')

        # C. Update / Reschedule Appointment
        if 'update_appointment' in request.POST:
            appointment_id = request.POST.get('appointment_id')
            new_status = request.POST.get('status')
            new_datetime_str = request.POST.get('appointment_date')

            appointment = get_object_or_404(Appointment, id=appointment_id, trainer=trainer)

            # Update status
            if new_status in dict(Appointment._meta.get_field('status').choices):
                appointment.status = new_status

            # Reschedule if datetime provided
            if new_datetime_str:
                # from <input type="datetime-local">
                try:
                    # datetime-local comes as 'YYYY-MM-DDTHH:MM'
                    naive_dt = datetime.fromisoformat(new_datetime_str)
                    appointment.appointment_date = timezone.make_aware(naive_dt, timezone.get_current_timezone())
                except Exception:
                    messages.error(request, "Invalid date/time format for rescheduling.")

            appointment.save()
            messages.success(request, "Appointment updated successfully.")
            return redirect('trainer_dashboard')

    # 3. Query data to show on dashboard

    # All trainees who have appointments with this trainer
    clients = Trainee.objects.filter(appointments__trainer=trainer).distinct()

    for client in clients:
        client.latest_diet = DietPlan.objects.filter(
            trainee=client
        ).order_by('-created_at').first()

        client.latest_workout = WorkoutPlan.objects.filter(
            trainee=client
        ).order_by('-created_at').first()


    # Appointments for this trainer
    now = timezone.now()
    upcoming_appointments = Appointment.objects.filter(
        trainer=trainer,
        appointment_date__gte=now
    ).order_by('appointment_date')

    past_appointments = Appointment.objects.filter(
        trainer=trainer,
        appointment_date__lt=now
    ).order_by('-appointment_date')[:10]  # last 10 for display

    # Latest plans per trainee (optional, for quick reference)
    latest_diet_plans = {
        dp.trainee_id: dp
        for dp in DietPlan.objects.filter(
            trainee__in=clients
        ).order_by('trainee_id', '-created_at')
    }

    latest_workout_plans = {
        wp.trainee_id: wp
        for wp in WorkoutPlan.objects.filter(
            trainee__in=clients
        ).order_by('trainee_id', '-created_at')
    }
    status_choices = Appointment._meta.get_field('status').choices

    context = {
        'trainer': trainer,
        'clients': clients,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'latest_diet_plans': latest_diet_plans,
        'latest_workout_plans': latest_workout_plans,
        'status_choices': status_choices,
    }

    return render(request, 'trainer_dashboard.html', context)


@login_required
def trainee_dashboard(request):
    trainee = get_object_or_404(Trainee, user=request.user)

    # Get active membership if any
    active_membership = (
        Membership.objects
        .filter(trainee=trainee, is_active=True)
        .order_by('-start_date')
        .first()
    )

    membership_form = None
    trainer_form = None

    if request.method == "POST":
        # A. Select membership
        if 'select_membership' in request.POST:
            membership_form = MembershipChoiceForm(request.POST)
            if membership_form.is_valid():
                membership_type = membership_form.cleaned_data['membership_type']
                duration_months = int(membership_form.cleaned_data['duration_months'])

                start_date = date.today()
                end_date = start_date + timedelta(days=30 * duration_months)

                base_prices = {
                    'silver': 1000,
                    'gold': 2000,
                    'platinum': 3000,
                }
                # Simple rule: base price * number of months
                amount = base_prices.get(membership_type, 0) * duration_months

                # Deactivate existing active memberships
                Membership.objects.filter(trainee=trainee, is_active=True).update(is_active=False)

                active_membership = Membership.objects.create(
                    trainee=trainee,
                    membership_type=membership_type,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=True,
                    amount=amount,
                )
                messages.success(request, "Membership selected successfully!")
                return redirect('membership_checkout', plan_type=membership_type)

        # B. Select trainer
        elif 'select_trainer' in request.POST and active_membership:
            trainer_form = TrainerChoiceForm(request.POST)
            if trainer_form.is_valid():
                trainer = trainer_form.cleaned_data['trainer']
                active_membership.trainer = trainer
                active_membership.save()

                # Initial demo appointment: tomorrow
                appt = Appointment.objects.create(
                    trainee=trainee,
                    trainer=trainer,
                    appointment_date=timezone.now() + timedelta(days=1),
                    status='Pending',
                    consultation_fee=active_membership.amount,
                    payment_status=False
                )
                # Link that appointment to membership
                active_membership.appointment = appt
                active_membership.save()

                messages.success(request, "Trainer selected and first appointment created!")
                return redirect('trainee_dashboard')

    # Forms for GET or if validation failed
    if not active_membership:
        membership_form = membership_form or MembershipChoiceForm()
    elif active_membership and not active_membership.trainer:
        trainer_form = trainer_form or TrainerChoiceForm()

    upcoming_appointments = Appointment.objects.filter(
        trainee=trainee,
        appointment_date__gte=timezone.now()
    ).order_by('appointment_date')

    past_appointments = Appointment.objects.filter(
        trainee=trainee,
        appointment_date__lt=timezone.now()
    ).order_by('-appointment_date')

    diet_plans = DietPlan.objects.filter(
        trainee=trainee
    ).order_by('-created_at')

    workout_plans = WorkoutPlan.objects.filter(
        trainee=trainee
    ).order_by('-created_at')

    context = {
        'trainee': trainee,
        'active_membership': active_membership,
        'membership_form': membership_form,
        'trainer_form': trainer_form,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'diet_plans': diet_plans,
        'workout_plans': workout_plans,
    }

    return render(request, 'trainee_dashboard.html', context)

def payment_gateway(request):
    return render(request, 'payment_gateway.html')

def membership_plans(request):
    return render(request, 'membership_plan.html')

@login_required
def book_appointment(request):
    trainee = get_object_or_404(Trainee, user=request.user)

    available_trainers = None
    selected_date = None
    selected_time = None

    if request.method == 'POST':
        selected_date = request.POST.get('date')
        selected_time = request.POST.get('time')

        if not selected_date or not selected_time:
            messages.error(request, "Please select both date and time.")
        else:
            try:
                slot_dt = datetime.strptime(
                    f"{selected_date} {selected_time}", "%Y-%m-%d %H:%M"
                )
            except ValueError:
                messages.error(request, "Invalid date or time format.")
            else:
                # Step 1: just checking availability
                if 'check_availability' in request.POST:
                    available_trainers = get_available_trainers(slot_dt)
                    if not available_trainers:
                        messages.warning(
                            request,
                            "No trainers are available at this time. Please try another slot."
                        )

                # Step 2: actually booking
                elif 'book_appointment' in request.POST:
                    trainer_id = request.POST.get('trainer')

                    if not trainer_id:
                        messages.error(request, "Please select a trainer.")
                        available_trainers = get_available_trainers(slot_dt)
                    else:
                        trainer = get_object_or_404(Trainer, id=trainer_id)

                        if not is_trainer_available(trainer, slot_dt):
                            messages.error(
                                request,
                                "That trainer is no longer available at this time. Please pick another slot."
                            )
                            available_trainers = get_available_trainers(slot_dt)
                        else:
                            Appointment.objects.create(
                                trainee=trainee,
                                trainer=trainer,
                                appointment_date=slot_dt,
                                status='Pending',
                                consultation_fee=100,  # adjust if you have pricing logic
                                payment_status=False,
                            )
                            messages.success(request, "Appointment booked successfully!")
                            return redirect('view_appointments')

    context = {
        'available_trainers': available_trainers,
        'selected_date': selected_date,
        'selected_time': selected_time,
    }
    return render(request, 'book_appointment.html', context)

@login_required
def view_appointments(request):
    trainee = get_object_or_404(Trainee, user=request.user)

    # Handle cancellation of appointments
    if request.method == 'POST':
        cancel_id = request.POST.get('cancel_id')
        if cancel_id:
            appt = get_object_or_404(Appointment, id=cancel_id, trainee=trainee)
            # Only allow cancelling upcoming, non-cancelled appointments
            if appt.appointment_date >= timezone.now() and appt.status != 'Cancelled':
                appt.status = 'Cancelled'
                appt.save()
                messages.success(request, "Appointment cancelled.")
            else:
                messages.error(request, "You cannot cancel this appointment.")

    upcoming_appointments = Appointment.objects.filter(
        trainee=trainee,
        appointment_date__gte=timezone.now()
    ).order_by('appointment_date')

    past_appointments = Appointment.objects.filter(
        trainee=trainee,
        appointment_date__lt=timezone.now()
    ).order_by('-appointment_date')

    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
    }
    return render(request, 'view_appointments.html', context)

def billing_info(request):
    return render(request, 'billing_info.html')

def profile(request):
    return render(request, 'profile.html')

def membership_details(request):
    return render(request, 'membership_details.html')

def trainer_list(request):
    trainer = Trainer.objects.all()
    return render(request, 'trainers.html', {'trainers': trainer})

def trainee_list(request):
    return render(request, 'trainees.html')

def register_trainer(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        phone_number = request.POST.get('phone_number')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        specialization = request.POST.get('specialization')
        profile_pic = request.FILES.get('profile_pic')

        # Basic validation
        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('register_trainer')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('register_trainer')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('register_trainer')

        # Create user as staff (trainer)
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.is_staff = True       # Important so they go to trainer_dashboard
        user.is_superuser = False  # Just in case
        user.save()

        # Create Trainer profile
        Trainer.objects.create(
            user=user,
            phone_number=phone_number,
            specialization=specialization,
            gender=gender,
            dob=dob,
            profile_pic=profile_pic
        )

        messages.success(request, "Trainer registered successfully. Please log in.")
        return redirect('login')

    return render(request, 'register_trainer.html')

def register_trainee(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        health_conditions = request.POST.get('health_conditions') == 'on'
        health_details = request.POST.get('health_details')
        if password == password_confirm:
            if User.objects.filter(username=username).exists():
                messages.info(request, "Username already taken")
                return redirect("register_trainee")
            elif User.objects.filter(email=email).exists():
                messages.info(request, "Email already registered")
                return redirect("register_trainee")
            else:
                user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
                user.save()
                trainee = Trainee.objects.create(user=user, phone_number=phone_number, dob=dob, gender=gender, health_conditions=health_conditions, health_details=health_details)
                trainee.save()
                return render(request, 'login.html', {'success_message': 'Trainee registered successfully. Please log in.'})
        else:
            return render(request, 'register_trainee.html', {'error_message': 'Passwords do not match.'})

    return render(request, 'register_trainee.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username = username, password = password)
        if user is not None:
            if user.is_staff == True:
                if user.is_superuser == True:
                    auth.login(request, user)
                    return redirect('admin_dashboard')
                else:
                    auth.login(request, user)
                    return redirect('trainer_dashboard')
            else:
                auth.login(request, user)
                return redirect('trainee_dashboard')
        else:
            messages.info(request, "Enter valid credentials")
            return redirect('login')
    return render(request, 'login.html', {'page':'login'})

def logout(request):
    auth.logout(request)
    return redirect('/')

@login_required
def trainee_profile(request):
    # Get the Trainee linked to the logged-in user
    trainee = get_object_or_404(Trainee, user=request.user)

    # Active membership (if any)
    active_membership = (
        Membership.objects
        .filter(trainee=trainee, is_active=True)
        .order_by('-start_date')
        .first()
    )

    # Stats and related info
    total_appointments = Appointment.objects.filter(trainee=trainee).count()
    completed_appointments = Appointment.objects.filter(
        trainee=trainee,
        status='Completed'
    ).count()

    upcoming_appointments = Appointment.objects.filter(
        trainee=trainee,
        appointment_date__gte=timezone.now()
    ).order_by('appointment_date')[:5]

    latest_diet_plan = (
        DietPlan.objects
        .filter(trainee=trainee)
        .order_by('-created_at')
        .first()
    )

    latest_workout_plan = (
        WorkoutPlan.objects
        .filter(trainee=trainee)
        .order_by('-created_at')
        .first()
    )

    context = {
        'trainee': trainee,
        'active_membership': active_membership,
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'upcoming_appointments': upcoming_appointments,
        'latest_diet_plan': latest_diet_plan,
        'latest_workout_plan': latest_workout_plan,
    }

    return render(request, 'trainee_profile.html', context)

@login_required
def membership_checkout(request, plan_type):
    """
    Dummy checkout/payment page.
    GET  -> show payment form
    POST -> 'process' payment, create membership, redirect to success
    """

    PLAN_CONFIG = {
        'silver': {
            'label': 'Silver',
            'price': 1999,
            'duration_months': 1,
            'tagline': "Perfect if you're just starting out",
        },
        'gold': {
            'label': 'Gold',
            'price': 2999,
            'duration_months': 1,
            'tagline': "For regular gym-goers who want more",
        },
        'platinum': {
            'label': 'Platinum',
            'price': 4499,
            'duration_months': 1,
            'tagline': "For serious athletes & transformation goals",
        },
    }

    if plan_type not in PLAN_CONFIG:
        raise Http404("Invalid membership type")

    config = PLAN_CONFIG[plan_type]

    # Ensure this user is a Trainee
    try:
        trainee = Trainee.objects.get(user=request.user)
    except Trainee.DoesNotExist:
        messages.error(request, "You need a trainee account to buy a membership.")
        return redirect('register_trainee')

    start_date = date.today()
    end_date = start_date + timedelta(days=30 * config['duration_months'])

    if request.method == "POST":
        # 💳 Dummy payment: we don't integrate gateway, we just assume success.

        # Deactivate any existing active membership
        Membership.objects.filter(trainee=trainee, is_active=True).update(is_active=False)

        membership = Membership.objects.create(
            trainee=trainee,
            membership_type=plan_type,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            amount=config['price'],
        )

        return redirect('membership_payment_success', membership_id=membership.id)

    # GET → show fake payment page
    context = {
        'plan_type': plan_type,
        'plan_label': config['label'],
        'tagline': config['tagline'],
        'price': config['price'],
        'duration_months': config['duration_months'],
        'start_date': start_date,
        'end_date': end_date,
        'trainee': trainee,
    }
    return render(request, 'membership_checkout.html', context)


@login_required
def membership_payment_success(request, membership_id):
    membership = get_object_or_404(
        Membership,
        id=membership_id,
        trainee__user=request.user
    )

    context = {
        'membership': membership,
    }
    return render(request, 'membership_success.html', context)

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from .models import (
    Trainee,
    Trainer,
    Appointment,
    Membership,
    Billing
)

@staff_member_required
def admin_dashboard(request):

    total_trainees = Trainee.objects.count()
    total_trainers = Trainer.objects.count()

    active_memberships = Membership.objects.filter(is_active=True).count()

    pending_appointments = Appointment.objects.filter(status="Pending").count()

    monthly_revenue = Billing.objects.filter(
        billing_date__month=timezone.now().month,
        is_paid=True
    ).aggregate(total=Sum("amount"))["total"] or 0

    recent_appointments = Appointment.objects.select_related(
        "trainee__user",
        "trainer__user"
    ).order_by("-appointment_date")[:5]

    context = {
        "total_trainees": total_trainees,
        "total_trainers": total_trainers,
        "active_memberships": active_memberships,
        "pending_appointments": pending_appointments,
        "monthly_revenue": monthly_revenue,
        "recent_appointments": recent_appointments,
    }

    return render(request, "admin_dashboard.html", context)
