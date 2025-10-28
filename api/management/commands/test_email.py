from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Test email configuration'

    def add_arguments(self, parser):
        parser.add_argument('--to', type=str, help='Email address to send test email to')
        parser.add_argument('--from', type=str, help='From email address')

    def handle(self, *args, **options):
        to_email = options.get('to') or 'test@example.com'
        from_email = options.get('from') or settings.DEFAULT_FROM_EMAIL
        
        self.stdout.write(f'Testing email configuration...')
        self.stdout.write(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'EMAIL_PORT: {settings.EMAIL_PORT}')
        self.stdout.write(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        
        try:
            send_mail(
                'Test Email from Sapphire',
                'This is a test email to verify SMTP configuration.',
                from_email,
                [to_email],
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully sent test email to {to_email}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send email: {e}')
            )
            self.stdout.write(
                self.style.WARNING('Make sure to configure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in your .env file')
            )
