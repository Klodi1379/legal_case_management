# billing/views_new.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import TimeEntry
from cases.models import Case
import logging

logger = logging.getLogger(__name__)

@login_required
def time_entry_create_simple(request):
    """A simplified view for creating time entries."""
    if request.method == 'POST':
        # Get form data
        case_id = request.POST.get('case')
        date_str = request.POST.get('date')
        hours_str = request.POST.get('hours')
        description = request.POST.get('description')
        rate_str = request.POST.get('rate')
        is_billable = request.POST.get('is_billable') == 'on'
        
        # Log the form data
        logger.info(f"Form data: case_id={case_id}, date={date_str}, hours={hours_str}, rate={rate_str}, is_billable={is_billable}")
        
        # Validate form data
        errors = []
        
        if not case_id:
            errors.append("Please select a case")
        
        if not date_str:
            errors.append("Please enter a date")
        
        if not hours_str:
            errors.append("Please enter hours")
        
        if not description:
            errors.append("Please enter a description")
        
        if not rate_str:
            errors.append("Please enter a rate")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            
            # Get cases for the form
            cases = Case.objects.filter(status='OPEN')
            
            return render(request, 'billing/time_entry_form_simple.html', {
                'cases': cases,
                'form_data': request.POST,
            })
        
        try:
            # Get the case
            case = Case.objects.get(id=case_id)
            
            # Parse date
            from datetime import datetime
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Parse hours and rate
            hours = float(hours_str)
            rate = float(rate_str)
            
            # Create time entry directly with raw SQL
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO billing_timeentry (case_id, user_id, date, hours, description, rate, is_billable)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    [case.id, request.user.id, date, hours, description, rate, is_billable]
                )
            
            messages.success(request, "Time entry created successfully")
            return redirect('billing:time_entry_list')
            
        except Exception as e:
            logger.error(f"Error creating time entry: {str(e)}", exc_info=True)
            messages.error(request, f"Error creating time entry: {str(e)}")
    
    # Get cases for the form
    cases = Case.objects.filter(status='OPEN')
    
    # Pre-populate with today's date
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')
    
    return render(request, 'billing/time_entry_form_simple.html', {
        'cases': cases,
        'form_data': {'date': today},
    })
