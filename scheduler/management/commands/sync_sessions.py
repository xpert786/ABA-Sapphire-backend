from django.core.management.base import BaseCommand
from scheduler.models import Session as ScheduledSession
from session.models import Session as TherapySession


class Command(BaseCommand):
    help = 'Sync existing scheduler sessions to therapy sessions'

    def handle(self, *args, **options):
        self.stdout.write('Starting session sync...')
        
        # Get all scheduled sessions
        scheduled_sessions = ScheduledSession.objects.all()
        
        created_count = 0
        skipped_count = 0
        
        for scheduled in scheduled_sessions:
            # Check if therapy session already exists
            existing = TherapySession.objects.filter(
                client=scheduled.client,
                staff=scheduled.staff,
                session_date=scheduled.session_date,
                start_time=scheduled.start_time,
                end_time=scheduled.end_time
            ).exists()
            
            if not existing:
                # Create the therapy session
                TherapySession.objects.create(
                    client=scheduled.client,
                    staff=scheduled.staff,
                    session_date=scheduled.session_date,
                    start_time=scheduled.start_time,
                    end_time=scheduled.end_time,
                    location='Scheduled Location',
                    service_type='ABA',
                    status='scheduled',
                    session_notes=scheduled.session_notes or ''
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created therapy session from schedule ID {scheduled.id}'
                    )
                )
            else:
                skipped_count += 1
                self.stdout.write(
                    f'⊘ Skipped schedule ID {scheduled.id} (already exists)'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Sync complete! Created: {created_count}, Skipped: {skipped_count}'
            )
        )

