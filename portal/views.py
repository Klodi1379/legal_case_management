# portal/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
from django.http import HttpResponseForbidden

from .models import PortalAccess, ClientTask, MessageThread, Message, Notification
from .forms import MessageForm, MessageThreadForm, ClientTaskForm
from cases.models import Case
from documents.models import Document
from clients.models import Client

def client_required(view_func):
    """
    Decorator to ensure only clients can access portal views.
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        # Check if user is a client
        if not request.user.is_client:
            messages.error(request, "Only clients can access the client portal.")
            return redirect('core:dashboard')

        # Check if user has portal access
        try:
            portal_access = request.user.portal_access
            if not portal_access.is_active:
                messages.error(request, "Your portal access is currently inactive. Please contact support.")
                return redirect('core:dashboard')

            # Update last login time
            portal_access.last_login = timezone.now()
            portal_access.save()

        except PortalAccess.DoesNotExist:
            messages.error(request, "You don't have portal access. Please contact support.")
            return redirect('core:dashboard')

        return view_func(request, *args, **kwargs)

    return wrapper

@client_required
def portal_home(request):
    """
    Portal home page - redirects to dashboard.
    """
    return redirect('portal:dashboard')

@client_required
def client_dashboard(request):
    """
    Client dashboard showing overview of cases, tasks, and notifications.
    """
    # Get client's cases
    try:
        client = Client.objects.filter(user=request.user).first()
        cases = Case.objects.filter(client=client).order_by('-open_date')

        # Get recent tasks
        tasks = ClientTask.objects.filter(
            case__in=cases,
            status__in=['PENDING', 'IN_PROGRESS']
        ).order_by('due_date')[:5]

        # Get unread messages count
        message_threads = MessageThread.objects.filter(
            participants=request.user
        ).annotate(
            unread=Count('messages', filter=~Q(messages__read_by=request.user))
        )

        unread_count = sum(thread.unread for thread in message_threads)

        # Get recent notifications
        notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:5]

        # Get recent documents
        documents = Document.objects.filter(
            case__in=cases
        ).order_by('-uploaded_at')[:5]

        context = {
            'client': client,
            'cases': cases,
            'tasks': tasks,
            'unread_messages': unread_count,
            'notifications': notifications,
            'documents': documents,
            'message_threads': message_threads.order_by('-updated_at')[:3]
        }

        return render(request, 'portal/dashboard.html', context)

    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return render(request, 'portal/dashboard.html', {'error': str(e)})

@client_required
def client_cases(request):
    """
    View for client to see all their cases.
    """
    try:
        client = Client.objects.filter(user=request.user).first()
        cases = Case.objects.filter(client=client).order_by('-open_date')

        return render(request, 'portal/cases.html', {'cases': cases})

    except Exception as e:
        messages.error(request, f"Error loading cases: {str(e)}")
        return render(request, 'portal/cases.html', {'error': str(e)})

@client_required
def client_case_detail(request, case_id):
    """
    Detailed view of a specific case for the client.
    """
    try:
        client = Client.objects.filter(user=request.user).first()
        case = get_object_or_404(Case, id=case_id, client=client)

        # Get case documents
        documents = Document.objects.filter(case=case).order_by('-uploaded_at')

        # Get case tasks
        tasks = ClientTask.objects.filter(case=case).order_by('due_date')

        # Get case messages
        message_threads = MessageThread.objects.filter(
            case=case,
            participants=request.user
        ).annotate(
            unread=Count('messages', filter=~Q(messages__read_by=request.user))
        ).order_by('-updated_at')

        context = {
            'case': case,
            'documents': documents,
            'tasks': tasks,
            'message_threads': message_threads
        }

        return render(request, 'portal/case_detail.html', context)

    except Exception as e:
        messages.error(request, f"Error loading case details: {str(e)}")
        return redirect('portal:cases')

@client_required
def client_documents(request):
    """
    View for client to see all documents across their cases.
    """
    try:
        client = Client.objects.filter(user=request.user).first()
        cases = Case.objects.filter(client=client)
        documents = Document.objects.filter(case__in=cases).order_by('-uploaded_at')

        return render(request, 'portal/documents.html', {'documents': documents})

    except Exception as e:
        messages.error(request, f"Error loading documents: {str(e)}")
        return render(request, 'portal/documents.html', {'error': str(e)})

@client_required
def client_messages(request):
    """
    View for client to see all message threads.
    """
    message_threads = MessageThread.objects.filter(
        participants=request.user
    ).annotate(
        unread=Count('messages', filter=~Q(messages__read_by=request.user))
    ).order_by('-updated_at')

    # Handle new thread creation
    if request.method == 'POST':
        form = MessageThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.created_by = request.user
            thread.save()

            # Add participants (client and case attorneys)
            thread.participants.add(request.user)

            if thread.case:
                # Add case team members
                for member in thread.case.team_members.all():
                    thread.participants.add(member.user)

            # Create initial message
            message = Message.objects.create(
                thread=thread,
                sender=request.user,
                content=form.cleaned_data['message']
            )

            # Create notifications for other participants
            for user in thread.participants.all():
                if user != request.user:
                    Notification.objects.create(
                        user=user,
                        notification_type='MESSAGE',
                        title=f"New message thread: {thread.subject}",
                        message=f"{request.user.get_full_name()} started a new conversation: {thread.subject}",
                        related_object_id=thread.id,
                        related_object_type='MessageThread'
                    )

            messages.success(request, "Message thread created successfully.")
            return redirect('portal:message_thread', thread_id=thread.id)
    else:
        form = MessageThreadForm()

    # Get client's cases for the form
    client = Client.objects.filter(user=request.user).first()
    cases = Case.objects.filter(client=client)
    form.fields['case'].queryset = cases

    return render(request, 'portal/messages.html', {
        'message_threads': message_threads,
        'form': form
    })

@client_required
def message_thread(request, thread_id):
    """
    View a specific message thread and add new messages.
    """
    thread = get_object_or_404(MessageThread, id=thread_id, participants=request.user)
    thread_messages = thread.messages.order_by('created_at')

    # Mark messages as read
    for message in thread_messages:
        if request.user not in message.read_by.all():
            message.mark_as_read(request.user)

    # Handle new message
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.thread = thread
            message.sender = request.user
            message.save()

            # Update thread timestamp
            thread.updated_at = timezone.now()
            thread.save()

            # Create notifications for other participants
            for user in thread.participants.all():
                if user != request.user:
                    Notification.objects.create(
                        user=user,
                        notification_type='MESSAGE',
                        title=f"New message in: {thread.subject}",
                        message=f"{request.user.get_full_name()} sent a new message in {thread.subject}",
                        related_object_id=thread.id,
                        related_object_type='MessageThread'
                    )

            messages.success(request, "Message sent successfully.")
            return redirect('portal:message_thread', thread_id=thread.id)
    else:
        form = MessageForm()

    return render(request, 'portal/message_thread.html', {
        'thread': thread,
        'messages': thread_messages,
        'form': form
    })

@client_required
def create_message(request):
    """
    Create a new message thread.
    """
    if request.method == 'POST':
        form = MessageThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.created_by = request.user
            thread.save()

            # Add participants
            thread.participants.add(request.user)

            if thread.case:
                # Add case team members
                for member in thread.case.team_members.all():
                    thread.participants.add(member.user)

            # Create initial message
            message = Message.objects.create(
                thread=thread,
                sender=request.user,
                content=form.cleaned_data['message']
            )

            messages.success(request, "Message thread created successfully.")
            return redirect('portal:message_thread', thread_id=thread.id)
    else:
        form = MessageThreadForm()

    # Get client's cases for the form
    client = Client.objects.filter(user=request.user).first()
    cases = Case.objects.filter(client=client)
    form.fields['case'].queryset = cases

    return render(request, 'portal/create_message.html', {'form': form})

@client_required
def client_profile(request):
    """
    View and update client profile information.
    """
    client = get_object_or_404(Client, user=request.user)

    return render(request, 'portal/profile.html', {'client': client})
