from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import AuditLog


def home(request):
    return render(request, 'core/home.html')


@login_required
def role_based_redirect(request):
    """
    Redirects users to the appropriate dashboard based on their role.
    """
    if request.user.is_client:
        return redirect('portal:dashboard')
    elif request.user.is_staff or request.user.is_superuser:
        return redirect('core:admin_dashboard')
    elif request.user.is_lawyer or request.user.role == 'ATTORNEY':
        return redirect('core:attorney_dashboard')
    else:
        return redirect('core:staff_dashboard')


@login_required
def dashboard(request):
    """
    Legacy dashboard view - redirects to role-based dashboard.
    """
    return role_based_redirect(request)


@login_required
def admin_dashboard(request):
    """
    Dashboard for administrators.
    """
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect('core:role_based_redirect')

    context = {
        'now': timezone.now(),
        'user_count': request.user._meta.model.objects.count(),
        'recent_audit_logs': AuditLog.objects.all().order_by('-timestamp')[:5]
    }
    return render(request, 'core/admin_dashboard.html', context)


@login_required
def attorney_dashboard(request):
    """
    Dashboard for attorneys and lawyers.
    """
    if not (request.user.is_lawyer or request.user.role == 'ATTORNEY'):
        return redirect('core:role_based_redirect')

    context = {
        'now': timezone.now()
    }
    return render(request, 'core/attorney_dashboard.html', context)


@login_required
def staff_dashboard(request):
    """
    Dashboard for general staff members.
    """
    if request.user.is_client:
        return redirect('core:role_based_redirect')

    context = {
        'now': timezone.now()
    }
    return render(request, 'core/staff_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def audit_log(request):
    """
    View for displaying the audit log.

    Only accessible to staff users.
    """
    # Get filters from request
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')

    # Base queryset
    logs = AuditLog.objects.all()

    # Apply filters
    if action_filter:
        logs = logs.filter(action=action_filter)

    if user_filter:
        logs = logs.filter(
            Q(user__username__icontains=user_filter) |
            Q(user__first_name__icontains=user_filter) |
            Q(user__last_name__icontains=user_filter)
        )

    # Paginate results
    paginator = Paginator(logs, 20)  # 20 logs per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Get action choices for filter dropdown
    action_choices = AuditLog.ACTION_CHOICES

    context = {
        'audit_logs': page_obj,
        'action_choices': action_choices,
        'selected_action': action_filter,
        'selected_user': user_filter,
    }

    return render(request, 'core/audit_log.html', context)