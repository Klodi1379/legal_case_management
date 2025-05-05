"""
Management command to clean up old data from the database.
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from core.models import AuditLog
from cases.models import CaseNote, CaseEvent
from documents.models import DocumentVersion
from ai_services.models import AIAnalysisRequest, AIAnalysisResult


class Command(BaseCommand):
    help = 'Clean up old data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Delete data older than this many days (default: 365)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--audit-logs',
            action='store_true',
            help='Clean up old audit logs',
        )
        parser.add_argument(
            '--document-versions',
            action='store_true',
            help='Clean up old document versions (keeping the latest)',
        )
        parser.add_argument(
            '--ai-results',
            action='store_true',
            help='Clean up old AI analysis results',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clean up all types of old data',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be deleted'))
        
        self.stdout.write(f'Cleaning up data older than {days} days (before {cutoff_date.date()})')
        self.stdout.write('')
        
        # Clean up audit logs
        if options['audit_logs'] or options['all']:
            self.clean_audit_logs(cutoff_date, dry_run)
        
        # Clean up old document versions
        if options['document_versions'] or options['all']:
            self.clean_document_versions(cutoff_date, dry_run)
        
        # Clean up old AI analysis results
        if options['ai_results'] or options['all']:
            self.clean_ai_results(cutoff_date, dry_run)
        
        if not any([options['audit_logs'], options['document_versions'], 
                    options['ai_results'], options['all']]):
            self.stdout.write('No cleanup options specified. Use --help to see available options.')
    
    def clean_audit_logs(self, cutoff_date, dry_run):
        """Clean up old audit logs."""
        self.stdout.write('Cleaning up audit logs...')
        
        # Keep authentication logs for longer
        auth_actions = ['login_success', 'login_failed', 'logout']
        
        # Regular audit logs (older than cutoff)
        regular_logs = AuditLog.objects.filter(
            created_at__lt=cutoff_date
        ).exclude(action__in=auth_actions)
        
        # Auth logs (keep for 2 years)
        auth_cutoff = timezone.now() - timedelta(days=730)
        auth_logs = AuditLog.objects.filter(
            created_at__lt=auth_cutoff,
            action__in=auth_actions
        )
        
        regular_count = regular_logs.count()
        auth_count = auth_logs.count()
        
        if dry_run:
            self.stdout.write(f'  Would delete {regular_count} regular audit logs')
            self.stdout.write(f'  Would delete {auth_count} authentication audit logs')
        else:
            regular_logs.delete()
            auth_logs.delete()
            self.stdout.write(self.style.SUCCESS(
                f'  Deleted {regular_count} regular audit logs'
            ))
            self.stdout.write(self.style.SUCCESS(
                f'  Deleted {auth_count} authentication audit logs'
            ))
    
    def clean_document_versions(self, cutoff_date, dry_run):
        """Clean up old document versions, keeping the latest version."""
        self.stdout.write('Cleaning up document versions...')
        
        # Get documents with multiple versions
        from django.db.models import Count, Max
        documents_with_versions = (
            DocumentVersion.objects
            .values('document')
            .annotate(version_count=Count('id'), latest_version=Max('version_number'))
            .filter(version_count__gt=1)
        )
        
        total_deleted = 0
        
        for doc_info in documents_with_versions:
            # Delete all but the latest version that are older than cutoff
            old_versions = DocumentVersion.objects.filter(
                document_id=doc_info['document'],
                created_at__lt=cutoff_date,
                version_number__lt=doc_info['latest_version']
            )
            
            count = old_versions.count()
            if count > 0:
                if dry_run:
                    self.stdout.write(f'  Would delete {count} old versions for document {doc_info["document"]}')
                else:
                    old_versions.delete()
                    total_deleted += count
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'  Deleted {total_deleted} old document versions'
            ))
    
    def clean_ai_results(self, cutoff_date, dry_run):
        """Clean up old AI analysis results."""
        self.stdout.write('Cleaning up AI analysis results...')
        
        # Delete results for failed analyses
        failed_results = AIAnalysisResult.objects.filter(
            has_error=True,
            created_at__lt=cutoff_date
        )
        
        # Delete results for completed analyses older than cutoff
        old_results = AIAnalysisResult.objects.filter(
            analysis_request__status='COMPLETED',
            created_at__lt=cutoff_date
        )
        
        failed_count = failed_results.count()
        old_count = old_results.count()
        
        if dry_run:
            self.stdout.write(f'  Would delete {failed_count} failed AI results')
            self.stdout.write(f'  Would delete {old_count} old AI results')
        else:
            failed_results.delete()
            old_results.delete()
            self.stdout.write(self.style.SUCCESS(
                f'  Deleted {failed_count} failed AI results'
            ))
            self.stdout.write(self.style.SUCCESS(
                f'  Deleted {old_count} old AI results'
            ))
