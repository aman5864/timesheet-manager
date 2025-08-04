from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
import random
from django.contrib.auth.decorators import login_required
from timesheet_backend.models import TimesheetEntry
from .forms import TimesheetEntryForm
from datetime import datetime, timedelta, date
from calendar import monthrange
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm
import io
import calendar
from openpyxl import Workbook
from django.http import HttpResponse, Http404
from collections import defaultdict
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils import timezone
from .forms import OTPBypassAuthenticationForm


User = get_user_model()

# ---------- User Registration ----------
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # User inactive until OTP verified
            user.save()

            # Generate OTP and store in session
            otp = random.randint(100000, 999999)
            request.session['otp'] = otp
            request.session['user_id'] = user.id

            # Send email
            send_mail(
                'Your OTP for Timesheet App',
                f'Your OTP is: {otp}',
                'no-reply@timesheetbyaman.com',
                [user.email],
                fail_silently=False,
            )

            return redirect('verify_otp')

    else:
        form = CustomUserCreationForm()

    return render(request, 'timesheet_app/register.html', {'form': form})


# ---------- OTP Verification ----------
def verify_otp(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please register or login again.')
        return redirect('login')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login')

    # ✅ Resend OTP logic
    if request.method == 'POST' and request.POST.get('resend') == '1':
        new_otp = random.randint(100000, 999999)
        request.session['otp'] = new_otp

        send_mail(
            subject='Your OTP Code',
            message=f'Your OTP is: {new_otp}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        messages.success(request, 'A new OTP has been sent to your email.')
        return redirect('verify_otp')  # Avoid resubmission

    # ✅ Handle OTP verification only if user submitted a non-empty otp field
    elif request.method == 'POST' and request.POST.get('otp'):
        input_otp = request.POST.get('otp').strip()
        session_otp = str(request.session.get('otp', '')).strip()

        if input_otp == session_otp:
            user.is_active = True
            user.save()
            login(request, user)

            request.session.pop('otp', None)
            request.session.pop('user_id', None)

            messages.success(request, 'Email verified and logged in successfully.')
            return redirect('week_view')
        else:
            messages.error(request, 'Invalid OTP.')

    # ✅ GET request or invalid/missing POST
    return render(request, 'timesheet_app/verify_otp.html')


# ---------- Views ----------
@login_required
def week_view(request, year=None, week=None):
    if not year or not week:
        today = datetime.today()
        year, week, _ = today.isocalendar()

    first_day = datetime.strptime(f'{year}-W{week}-1', "%G-W%V-%u").date()
    week_dates = [first_day + timedelta(days=i) for i in range(7)]

    entries = TimesheetEntry.objects.filter(user=request.user, date__range=[week_dates[0], week_dates[-1]])
    entry_map = defaultdict(list)
    for entry in entries:
        entry_map[entry.date].append(entry)

    week_data = []
    for day in week_dates:
        entries = entry_map.get(day, [])
        total_time = sum(entry.time_taken for entry in entries)
        week_data.append({
            'date': day,
            'day_name': day.strftime('%A'),
            'entries': entries,
            'total_time': total_time,
            'is_weekend': day.weekday() >= 5,
        })

    context = {
        'week_data': week_data,
        'week': week,
        'year': year,
        'prev_week': (week_dates[0] - timedelta(days=7)).isocalendar(),
        'next_week': (week_dates[0] + timedelta(days=7)).isocalendar(),
    }
    return render(request, 'timesheet_app/timesheet_list.html', context)


@login_required
def create_entry(request):
    if request.method == 'POST':
        form = TimesheetEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user  # 🔥 associate with logged-in user
            entry.full_clean()
            entry.save()
            return redirect('week_view')
    else:
        form = TimesheetEntryForm()
    return render(request, 'timesheet_app/timesheet_form.html', {'form': form})


@login_required
def update_entry(request, pk):
    entry = get_object_or_404(TimesheetEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TimesheetEntryForm(request.POST, instance=entry)
        if form.is_valid():
            updated_entry = form.save(commit=False)
            updated_entry.user = request.user  # 🔥 ensure user stays the same
            updated_entry.save()
            return redirect('week_view')
    else:
        form = TimesheetEntryForm(instance=entry)
    return render(request, 'timesheet_app/timesheet_form.html', {'form': form, 'update': True})


@login_required
def delete_entry(request, pk):
    entry = get_object_or_404(TimesheetEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        entry.delete()
        return redirect('week_view')
    return render(request, 'timesheet_app/confirm_delete.html', {'entry': entry})


@login_required
def month_view(request, year=None, month=None):
    # Fallback to current month if not specified
    if not year or not month:
        today = timezone.now().date()
        year, month = today.year, today.month

    first_day = date(year, month, 1)
    last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

    all_days = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]
    entries = TimesheetEntry.objects.filter(user=request.user, date__range=[first_day, last_day])
    
    entry_map = defaultdict(list)
    for entry in entries:
        entry_map[entry.date].append(entry)

    days = []
    for day in all_days:
        entries = entry_map.get(day, [])
        total_time = sum(entry.time_taken for entry in entries)
        days.append({
            'date': day,
            'day_name': day.strftime('%A'),
            'entries': entries,
            'total_time': total_time,
            'is_weekend': day.weekday() >= 5,
        })

    context = {
        'days': days,
        'month': month,
        'year': year,
        'month_name': first_day.strftime('%B'),
        'prev_month': ((first_day - timedelta(days=1)).year, (first_day - timedelta(days=1)).month),
        'next_month': ((last_day + timedelta(days=1)).year, (last_day + timedelta(days=1)).month),
    }
    return render(request, 'timesheet_app/month_view.html', context)


@login_required
def export_month_excel(request, year, month):
    # Only allow downloads triggered by JavaScript
    if request.GET.get("js") != "1":
        raise Http404("Invalid or direct download not allowed.")

    year = int(year)
    month = int(month)
    include_time = request.GET.get("include_time", "yes") == "yes"

    start_date = datetime(year, month, 1).date()
    end_date = start_date.replace(day=monthrange(year, month)[1])

    entries = TimesheetEntry.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    ).order_by('date')

    wb = Workbook()
    ws = wb.active
    ws.title = f"{calendar.month_name[month]} {year}"

    # Header
    headers = ["Date", "Day", "Task", "Ticket", "Description"]
    if include_time:
        headers.insert(4, "Time Spent (hrs)")
    ws.append(headers)

    # Group entries by date
    grouped = {}
    for entry in entries:
        grouped.setdefault(entry.date, []).append(entry)

    # Populate rows for each day of the month
    for day in (start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)):
        day_name = day.strftime("%A")
        day_entries = grouped.get(day, [])

        if day.weekday() >= 5:
            ws.append(
                [day, day_name, "Weekly Off", "", "", ""] if include_time else
                [day, day_name, "Weekly Off", "", ""]
            )
        elif day_entries:
            for entry in day_entries:
                row = [entry.date, day_name, entry.task, entry.ticket_number, entry.description]
                if include_time:
                    row.insert(4, entry.time_taken)
                ws.append(row)
        else:
            ws.append(
                [day, day_name, "No entry", "", "", ""] if include_time else
                [day, day_name, "No entry", "", ""]
            )

    # Generate and return Excel response
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Timesheet_{year}_{month}.xlsx"
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@require_GET
@login_required
def is_weekend(request):
    date_str = request.GET.get('date')
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        is_weekend = date_obj.weekday() >= 5  # Saturday = 5, Sunday = 6
        return JsonResponse({'is_weekend': is_weekend})
    except ValueError:
        return JsonResponse({'error': 'Invalid date'}, status=400)
    
from .forms import OTPBypassAuthenticationForm

def custom_login_view(request):
    if request.method == 'POST':
        form = OTPBypassAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)

            if user:
                if user.is_active:
                    login(request, user)
                    return redirect('week_view')
                else:
                    # User is not verified, resend OTP
                    otp = random.randint(100000, 999999)
                    request.session['otp'] = otp
                    request.session['user_id'] = user.id

                    send_mail(
                        'Your OTP for Timesheet Verification',
                        f'Your OTP is: {otp}',
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False
                    )

                    messages.info(request, "Your account is not verified. A new OTP has been sent.")
                    return redirect('verify_otp')
            else:
                messages.error(request, 'Invalid credentials.')
    else:
        form = OTPBypassAuthenticationForm()

    return render(request, 'timesheet_app/login.html', {'form': form})