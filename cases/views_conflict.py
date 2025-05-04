"""
Views for conflict checking in the legal case management system.

This module provides views for performing and managing conflict checks
for legal cases.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse

from .models import Case, ConflictCheck
from .forms import ConflictCheckForm

@login_required
@permission_required('cases.add_conflictcheck')
def conflict_check_create(request, case_id):
    """
    Create a new conflict check for a case.
    
    Args:
        request: The HTTP request
        case_id: The ID of the case to check
        
    Returns:
        Rendered conflict check form or redirects to case detail
    """
    case = get_object_or_404(Case, id=case_id)
    
    if request.method == 'POST':
        form = ConflictCheckForm(request.POST)
        if form.is_valid():
            conflict_check = form.save(commit=False)
            conflict_check.case = case
            conflict_check.checked_by = request.user
            conflict_check.save()
            
            # Perform the check
            results = conflict_check.perform_check()
            
            if results['conflicts_found']:
                messages.warning(
                    request, 
                    f"Potential conflicts found! Please review the {len(results['potential_conflicts'])} "
                    f"potential conflicts and resolve them."
                )
                return redirect('cases:conflict_check_detail', check_id=conflict_check.id)
            else:
                messages.success(request, "No conflicts found.")
                return redirect('cases:case_detail', case_id=case.id)
    else:
        form = ConflictCheckForm(initial={
            'check_source': 'AUTOMATED',
            'parties_checked': [
                {'name': case.client.get_full_name(), 'type': 'CLIENT'},
            ]
        })
    
    return render(request, 'cases/conflict_check_form.html', {
        'form': form,
        'case': case,
        'title': 'New Conflict Check'
    })

@login_required
@permission_required('cases.view_conflictcheck')
def conflict_check_detail(request, check_id):
    """
    View details of a conflict check.
    
    Args:
        request: The HTTP request
        check_id: The ID of the conflict check
        
    Returns:
        Rendered conflict check detail page
    """
    conflict_check = get_object_or_404(ConflictCheck, id=check_id)
    
    # Check permissions
    if not request.user.has_perm('cases.view_any_conflictcheck') and conflict_check.checked_by != request.user:
        messages.error(request, "You don't have permission to view this conflict check.")
        return redirect('cases:case_detail', case_id=conflict_check.case.id)
    
    return render(request, 'cases/conflict_check_detail.html', {
        'conflict_check': conflict_check,
        'case': conflict_check.case,
        'title': 'Conflict Check Details'
    })

@login_required
@permission_required('cases.change_conflictcheck')
@require_POST
def conflict_check_resolve(request, check_id):
    """
    Resolve a conflict check.
    
    Args:
        request: The HTTP request
        check_id: The ID of the conflict check
        
    Returns:
        Redirects to conflict check detail or case detail
    """
    conflict_check = get_object_or_404(ConflictCheck, id=check_id)
    
    # Check permissions
    if not request.user.has_perm('cases.change_any_conflictcheck') and conflict_check.checked_by != request.user:
        messages.error(request, "You don't have permission to resolve this conflict check.")
        return redirect('cases:conflict_check_detail', check_id=check_id)
    
    resolution_status = request.POST.get('resolution_status')
    resolution_notes = request.POST.get('resolution_notes', '')
    
    if resolution_status not in dict(ConflictCheck.RESOLUTION_CHOICES):
        messages.error(request, "Invalid resolution status.")
        return redirect('cases:conflict_check_detail', check_id=check_id)
    
    conflict_check.resolution_status = resolution_status
    conflict_check.resolution_notes = resolution_notes
    conflict_check.resolved_by = request.user
    conflict_check.resolution_date = timezone.now()
    conflict_check.save()
    
    messages.success(request, "Conflict check resolved successfully.")
    return redirect('cases:case_detail', case_id=conflict_check.case.id)

@login_required
@permission_required('cases.view_conflictcheck')
def conflict_check_list(request, case_id=None):
    """
    List conflict checks, optionally filtered by case.
    
    Args:
        request: The HTTP request
        case_id: Optional case ID to filter by
        
    Returns:
        Rendered conflict check list page
    """
    if case_id:
        case = get_object_or_404(Case, id=case_id)
        conflict_checks = ConflictCheck.objects.filter(case=case)
        title = f"Conflict Checks for {case.title}"
    else:
        case = None
        # If user has permission to view any conflict check, show all
        if request.user.has_perm('cases.view_any_conflictcheck'):
            conflict_checks = ConflictCheck.objects.all()
        else:
            # Otherwise, show only those performed by the user
            conflict_checks = ConflictCheck.objects.filter(checked_by=request.user)
        title = "All Conflict Checks"
    
    conflict_checks = conflict_checks.select_related('case', 'checked_by', 'resolved_by').order_by('-check_date')
    
    return render(request, 'cases/conflict_check_list.html', {
        'conflict_checks': conflict_checks,
        'case': case,
        'title': title
    })
