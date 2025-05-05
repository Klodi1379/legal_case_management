"""
Management command to generate an encryption key for document encryption.
"""
from django.core.management.base import BaseCommand
from core.utils.encryption import generate_encryption_key


class Command(BaseCommand):
    help = 'Generate a new encryption key for document encryption'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show',
            action='store_true',
            help='Show the generated key in the console',
        )
        parser.add_argument(
            '--save',
            type=str,
            help='Save the generated key to a file',
        )

    def handle(self, *args, **options):
        self.stdout.write('Generating new encryption key...')
        
        # Generate the key
        key = generate_encryption_key()
        
        # Show the key if requested
        if options['show']:
            self.stdout.write(self.style.WARNING(
                'WARNING: This key should be kept secret and never committed to version control!'
            ))
            self.stdout.write(f'Encryption key: {key}')
            self.stdout.write('')
        
        # Save to file if requested
        if options['save']:
            try:
                with open(options['save'], 'w') as f:
                    f.write(key)
                self.stdout.write(self.style.SUCCESS(
                    f'Encryption key saved to: {options["save"]}'
                ))
                self.stdout.write(self.style.WARNING(
                    'WARNING: Make sure to protect this file and never commit it to version control!'
                ))
            except Exception as e:
                self.stderr.write(self.style.ERROR(
                    f'Error saving key to file: {str(e)}'
                ))
                return
        
        # If neither show nor save, just confirm generation
        if not options['show'] and not options['save']:
            self.stdout.write(self.style.SUCCESS('Encryption key generated successfully!'))
            self.stdout.write('Use --show to display it or --save to save it to a file.')
        
        # Always show instructions
        self.stdout.write('')
        self.stdout.write('To use this key:')
        self.stdout.write('1. Add it to your .env file as: DOCUMENT_ENCRYPTION_KEY=<your_key>')
        self.stdout.write('2. Or set it as an environment variable')
        self.stdout.write('3. Never commit the key to version control!')
