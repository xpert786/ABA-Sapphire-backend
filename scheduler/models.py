from django.db import models
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save

User = get_user_model()

class Client(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        try:
            return self.name
        except UnicodeEncodeError:
            return f"Client {self.id}"

# Signal to create a user automatically
@receiver(post_save, sender=Client)
def create_user_for_client(sender, instance, created, **kwargs):
    if created:
        User.objects.create(
            username=instance.name,  # or instance.name
            email=instance.email,
            role='Clients/Parent',            # assuming you have a client role
            password='defaultpassword'  # or generate a random password
        )

class Session(models.Model):


    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions_as_client',
        limit_choices_to={'role__name': 'Clients/Parent'}
    )
    
    # Only users with role 'rbt' or 'bcba' (staff)
    staff = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sessions_as_staff',
        limit_choices_to={'role__name__in': ['RBT', 'BCBA']}  # must be a list
    )
    
    # Treatment plan reference (optional)
    treatment_plan = models.ForeignKey(
        'treatment_plan.TreatmentPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
        help_text='Treatment plan this session is scheduled for'
    )
    
    session_date = models.DateField()       # Separate date field
    start_time = models.TimeField()         # Only time
    end_time = models.TimeField()
    session_notes = models.TextField(blank=True, null=True) 
    duration = models.DurationField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_time']
        unique_together = ['staff', 'start_time', 'end_time']  # basic conflict prevention

    def __str__(self):
        try:
            return f"{self.client.username} - {self.staff.username if self.staff else 'No Staff'} ({self.start_time})"
        except UnicodeEncodeError:
            return f"Session {self.id} - {self.start_time}"

class SessionLog(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    behavior = models.TextField()
    antecedent = models.TextField()
    consequence = models.TextField()
    reinforcement = models.TextField(blank=True)
    client_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class TimeTracker(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    @property
    def duration(self):
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60  # minutes
        return 0


# Signal to automatically create a therapy session when a schedule is created
@receiver(post_save, sender=Session)
def create_therapy_session_from_schedule(sender, instance, created, **kwargs):
    """
    Automatically creates a therapy session in the session app
    whenever a new schedule is created in the scheduler app.
    """
    if created:
        try:
            # Import session app models
            from session.models import Session as TherapySession
            
            # Check if therapy session already exists for this schedule
            existing = TherapySession.objects.filter(
                client=instance.client,
                staff=instance.staff,
                session_date=instance.session_date,
                start_time=instance.start_time,
                end_time=instance.end_time
            ).exists()
            
            if not existing:
                # Create the therapy session automatically
                TherapySession.objects.create(
                    client=instance.client,
                    staff=instance.staff,
                    session_date=instance.session_date,
                    start_time=instance.start_time,
                    end_time=instance.end_time,
                    location='Scheduled Location',  # Default location
                    service_type='ABA',
                    status='scheduled',  # Status is 'scheduled', not 'in_progress'
                    session_notes=instance.session_notes or ''
                )
                print(f"[SUCCESS] Therapy session automatically created from schedule ID {instance.id}")
        except Exception as e:
            # Log error but don't break the schedule creation
            print(f"[ERROR] Failed to create therapy session from schedule: {str(e)}")