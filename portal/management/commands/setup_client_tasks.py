"""
Management command to set up initial tasks for clients.

This command creates initial tasks for clients based on their cases.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from clients.models import Client
from cases.models import Case
from portal.models import ClientTask, Notification

class Command(BaseCommand):
    help = 'Sets up initial tasks for clients based on their cases'

    def add_arguments(self, parser):
        parser.add_argument(
            '--case-id',
            type=int,
            help='Create tasks only for a specific case ID'
        )
        parser.add_argument(
            '--notify',
            action='store_true',
            help='Create notifications for new tasks'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Setting up initial client tasks...'))

        case_id = options.get('case_id')
        notify = options.get('notify', False)

        # Set up client tasks
        with transaction.atomic():
            if case_id:
                # Create tasks for specific case
                try:
                    case = Case.objects.get(id=case_id)
                    task_count = self._setup_tasks_for_case(case, notify)
                    self.stdout.write(self.style.SUCCESS(
                        f'Created {task_count} tasks for case {case.title}'
                    ))
                except Case.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'Case with ID {case_id} not found'))
                    return
            else:
                # Create tasks for all cases
                task_count = self._setup_tasks_for_all_cases(notify)
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully created {task_count} client tasks'
                ))

    def _setup_tasks_for_all_cases(self, notify):
        """Set up tasks for all open cases."""
        count = 0

        # Get all open cases
        cases = Case.objects.filter(status='OPEN')

        for case in cases:
            count += self._setup_tasks_for_case(case, notify)

            if count % 10 == 0:
                self.stdout.write(f'Created {count} tasks')

        return count

    def _setup_tasks_for_case(self, case, notify):
        """Set up initial tasks for a specific case."""
        count = 0

        # Skip if case has no client
        if not case.client or not case.client.user:
            return 0

        # Create document review task if case has documents
        if case.documents.exists() and not ClientTask.objects.filter(
            case=case,
            title='Review Case Documents'
        ).exists():
            task = ClientTask.objects.create(
                case=case,
                title='Review Case Documents',
                description='Please review the documents uploaded to your case and let us know if you have any questions.',
                assigned_to=case.client.user,
                due_date=timezone.now() + timezone.timedelta(days=7),
                status='PENDING'
            )
            count += 1

            # Create notification if requested
            if notify:
                Notification.objects.create(
                    user=case.client.user,
                    notification_type='TASK',
                    title='New Task: Review Case Documents',
                    message=f'You have a new task for case {case.title}: Review Case Documents',
                    related_object_id=task.id,
                    related_object_type='ClientTask'
                )

        # Create information gathering task for all cases
        if not ClientTask.objects.filter(
            case=case,
            title='Provide Additional Information'
        ).exists():
            task = ClientTask.objects.create(
                case=case,
                title='Provide Additional Information',
                description='Please provide any additional information that might be relevant to your case.',
                assigned_to=case.client.user,
                due_date=timezone.now() + timezone.timedelta(days=14),
                status='PENDING'
            )
            count += 1

            # Create notification if requested
            if notify:
                Notification.objects.create(
                    user=case.client.user,
                    notification_type='TASK',
                    title='New Task: Provide Additional Information',
                    message=f'You have a new task for case {case.title}: Provide Additional Information',
                    related_object_id=task.id,
                    related_object_type='ClientTask'
                )

        return count
