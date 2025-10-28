from django.contrib.auth import get_user_model
from rest_framework import serializers, generics, status

from .models import CustomUser, Role, Permission, Certificate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re
User = get_user_model()

# Register serializer
class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        required=False,
        allow_null=True
    )
    supervisor = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role__name__in=['Admin', 'Superadmin']).order_by('-id'),
        required=False,
        allow_null=True
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = CustomUser
        fields = [
            'id', 'name', 'username', 'email', 'role', 'password', 'phone', 
            'business_name', 'business_address', 'business_website', 
            'street', 'city', 'state', 'zip_code', 'country',
            'session_duration', 'goals', 'session_focus', 'telehealth', 'session_note', 'supervisor',
            # Personal info
            'dob', 'gender', 'primary_diagnosis', 'secondary_diagnosis', 'staff_id',
            # Parent/Guardian info
            'parent_name', 'parent_relationship', 'parent_phone', 'parent_email', 'prefered_contact_method',
            # Clinical info
            'assigned_bcba', 'assigned_rbt', 'preferred_session_time', 'preferred_session_duration',
            'service_location', 'preferred_session_telehealth',
            # Document uploads
            'consent_for_treatment', 'hippa_authorization', 'insurance_card', 'physician_referral',
            'previous_assessment', 'iep',
            # Emergency contact info
            'primary_physician', 'emergency_phone_number', 'allergies', 'medication', 'special_considerations'
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        
        # Allow only letters and numbers
        if not re.match(r'^[a-zA-Z0-9]+$', value):
            raise serializers.ValidationError("Username can only contain letters and numbers.")
        
        return value

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate_supervisor(self, value):
        if value and value.role.name not in ['Admin', 'Superadmin']:
            raise serializers.ValidationError("Supervisor must have the role 'Admin' or 'Superadmin'.")
        return value

    def validate_phone(self, value):
        if not value:
            return value  # allow blank/null
        # Allow optional + at the start, then digits
        pattern = r'^\+?\d{10,15}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("Phone number must be 10-15 digits and can start with +.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        supervisor = validated_data.pop('supervisor', None)
        
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.is_staff = True
        
        # Get the logged-in user (the one creating this user)
        logged_in_user = self.context['request'].user
        
        # Auto-assign supervisor if not provided
        if not supervisor and user.role:
            if user.role.name in ['RBT', 'BCBA', 'Clients/Parent']:
                # Use the logged-in user as supervisor if they are Admin/Superadmin
                if logged_in_user.role and logged_in_user.role.name in ['Admin']:
                    user.supervisor = logged_in_user
                else:
                    # Fallback to first available Admin
                    admin_supervisor = CustomUser.objects.filter(
                        role__name='Admin',
                        status='Active'
                    ).first()
                    if admin_supervisor:
                        user.supervisor = admin_supervisor
            elif user.role.name == 'Admin':
                # Use logged-in user if they are Superadmin, otherwise find Superadmin
                if logged_in_user.role and logged_in_user.role.name == 'Superadmin':
                    user.supervisor = logged_in_user
                else:
                    superadmin_supervisor = CustomUser.objects.filter(
                        role__name='Superadmin',
                        status='Active'
                    ).first()
                    if superadmin_supervisor:
                        user.supervisor = superadmin_supervisor
        elif supervisor:
            # Use provided supervisor
            user.supervisor = supervisor
            
        user.save()
        return user

# Certificate serializer (moved before UserSerializer for proper reference)
class CertificateSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Certificate
        fields = [
            'id', 
            'user', 
            'user_name',
            'name', 
            'certificate_file', 
            'certificate_number', 
            'certificate_issue_date', 
            'certificate_expiration_date', 
            'for_lifetime',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_name']

    def validate(self, data):
        # If not for lifetime, expiration date is required
        if not data.get('for_lifetime') and not data.get('certificate_expiration_date'):
            raise serializers.ValidationError({
                'certificate_expiration_date': 'Expiration date is required if certificate is not for lifetime.'
            })
        return data


# User serializer
class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='role.name', read_only=True)
    extra_permissions = serializers.SlugRelatedField(
        many=True,
        slug_field='codename',
        queryset=Permission.objects.all(),
        required=False
    )
    client_count = serializers.SerializerMethodField()
    certificates = CertificateSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'role', 'extra_permissions', 'name', 'status', 
            'client_count', 'phone', 'business_name', 'business_address', 
            'business_website', 'password', 'certificates', 'street', 'city', 'state', 'zip_code', 'country',
            # Personal info
            'dob', 'gender', 'primary_diagnosis', 'secondary_diagnosis', 'staff_id',
            # Parent/Guardian info
            'parent_name', 'parent_relationship', 'parent_phone', 'parent_email', 'prefered_contact_method',
            # Clinical info
            'assigned_bcba', 'assigned_rbt', 'preferred_session_time', 'preferred_session_duration',
            'service_location', 'preferred_session_telehealth',
            # Document uploads
            'consent_for_treatment', 'hippa_authorization', 'insurance_card', 'physician_referral',
            'previous_assessment', 'iep',
            # Emergency contact info
            'primary_physician', 'emergency_phone_number', 'allergies', 'medication', 'special_considerations',
            # Session info
            'session_duration', 'goals', 'session_focus', 'telehealth', 'session_note',
            # System info
            'supervisor', 'date_joined', 'last_login', 'is_active', 'is_staff'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {'password': {'required': False}}
    def get_client_count(self, obj):
        return CustomUser.objects.filter(
            supervisor=obj,
            role__name="Clients/Parent"
        ).count()

    def validate_status(self, value):
        valid_statuses = [choice[0] for choice in CustomUser.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError("Invalid status")
        return value

    def validate_username(self, value):
        user = self.instance
        if CustomUser.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def update(self, instance, validated_data):
        # Handle extra_permissions separately
        extra_permissions = validated_data.pop('extra_permissions', None)
        password = validated_data.pop('password', None)

        # Update normal fields
        user = super().update(instance, validated_data)

        # Update extra_permissions if provided
        if extra_permissions is not None:
            user.extra_permissions.set(extra_permissions)

        # Update password if provided
        if password:
            user.set_password(password)  # hashed password
            user.plain_password = password  # store plain password
            user.save()

        return user

# Assign permissions serializer
class AssignPermissionSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    permissions = serializers.ListField(child=serializers.CharField(max_length=100))

# Role serializer
class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SlugRelatedField(
        many=True,
        slug_field='codename',
        queryset=Permission.objects.all()
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'permissions']

# JWT Token serializer
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # First, perform the default validation (username/password)
        data = super().validate(attrs)

        # Check if the user's status is 'active'
        if self.user.status != 'Active':
            raise serializers.ValidationError("Your account is not active. Please contact admin.")

        # Add custom fields to the response
        data.update({
            "user_id": self.user.id,
            "username": self.user.username,
            "role": self.user.role.name if self.user.role else None,
        })
        return data

# Edit status 
class UserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['status']  # only allow editing status

    def validate_status(self, value):
        valid_statuses = [choice[0] for choice in CustomUser.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError("Invalid status")
        return value
    
class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

class SetNewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Password fields didn't match."})
        return attrs
