from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history.models import HistoricalRecords
from django.contrib.auth import get_user_model
import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
# Permission model
class Permission(models.Model):
    name = models.CharField(max_length=100)
    codename = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# Role model
class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return self.name

# Custom user model
class CustomUser(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        limit_choices_to={'role__name__in': ['Admin', 'Superadmin']}  # Admin and Super Admin users can be supervisors
    )
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Pending', 'Pending'),
        ('Suspended', 'Suspended'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Active'
    )

    # Personal info
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    primary_diagnosis = models.TextField(blank=True, null=True)
    secondary_diagnosis = models.TextField(blank=True, null=True)
    street = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    zip_code = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    staff_id = models.CharField(max_length=255, blank=True, null=True)
    # Parent/Guardian info
    parent_name = models.CharField(max_length=255, blank=True, null=True)
    parent_relationship = models.CharField(max_length=255, blank=True, null=True)
    parent_phone = models.CharField(max_length=15, blank=True, null=True)
    parent_email = models.EmailField(blank=True, null=True)
    prefered_contact_method = models.CharField(max_length=255, blank=True, null=True)

    # Clinical info
    assigned_bcba = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='bcba_clients')
    assigned_rbt = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='rbt_clients')
    preferred_session_time = models.CharField(max_length=255, blank=True, null=True)
    preferred_session_duration = models.IntegerField(blank=True, null=True)
    service_location = models.CharField(max_length=255, blank=True, null=True)
    preferred_session_telehealth = models.BooleanField(default=False)

    # Intake document upload
    consent_for_treatment = models.FileField(upload_to='intake_documents/', blank=True, null=True)
    hippa_authorization = models.FileField(upload_to='intake_documents/', blank=True, null=True)
    insurance_card = models.FileField(upload_to='intake_documents/', blank=True, null=True)
    physician_referral = models.FileField(upload_to='intake_documents/', blank=True, null=True)
    previous_assessment = models.FileField(upload_to='intake_documents/', blank=True, null=True)
    iep = models.FileField(upload_to='intake_documents/', blank=True, null=True)
    # Emergency contact info
    primary_physician = models.CharField(max_length=255, blank=True, null=True)
    emergency_phone_number = models.CharField(max_length=15, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    medication = models.TextField(blank=True, null=True)
    special_considerations = models.TextField(blank=True, null=True)

    phone = models.CharField(max_length=15, blank=True, null=True)
    business_name = models.CharField(max_length=255, blank=True, null=True)
    business_address = models.TextField(blank=True, null=True)
    business_website = models.URLField(blank=True, null=True)

    session_duration = models.IntegerField(blank=True, null=True)
    goals = models.TextField(blank=True, null=True)
    session_focus = models.TextField(blank=True, null=True)
    telehealth = models.BooleanField(default=False)
    session_note = models.TextField(blank=True, null=True)

    extra_permissions = models.ManyToManyField(Permission, blank=True)
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        # Auto-generate staff_id if not provided
        if not self.staff_id:
            # Get the last staff_id from the database
            last_user = CustomUser.objects.filter(staff_id__isnull=False).order_by('-id').first()
            
            if last_user and last_user.staff_id:
                # Extract the numeric part from the last staff_id
                try:
                    last_number = int(last_user.staff_id.replace('STAFF', ''))
                    new_number = last_number + 1
                except (ValueError, AttributeError):
                    new_number = 1
            else:
                new_number = 1
            
            # Generate new staff_id with leading zeros (e.g., STAFF0001)
            self.staff_id = f"STAFF{new_number:04d}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role.name if self.role else 'No Role'})"

# Assign roles to users
class UserRoleAssignment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

# Assign extra permissions to users
class UserPermission(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)


class OTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)  # 6-digit OTP
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Use timezone.now() for aware datetime
            self.expires_at = timezone.now() + timedelta(minutes=5)  # OTP valid for 5 min
        super().save(*args, **kwargs)

    def is_valid(self):
        # Compare with timezone-aware datetime
        return timezone.now() <= self.expires_at


# Certificate model for multiple certificates per user
class Certificate(models.Model):
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='certificates'
    )
    name = models.CharField(max_length=255, help_text="Certificate name/type")
    certificate_file = models.FileField(upload_to='staff_certificates/', blank=True, null=True)
    certificate_number = models.CharField(max_length=255, blank=True, null=True)
    certificate_issue_date = models.DateField(blank=True, null=True)
    certificate_expiration_date = models.DateField(blank=True, null=True)
    for_lifetime = models.BooleanField(default=False, help_text="Check if certificate is valid for lifetime")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.user.username}"
