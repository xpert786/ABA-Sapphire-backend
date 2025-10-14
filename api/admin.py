from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Role, Permission, UserRoleAssignment, UserPermission, Certificate


# ---- Custom Multiple Permission Filter ----
class PermissionListFilter(admin.SimpleListFilter):
    title = 'User Extra Permissions'
    parameter_name = 'permissions'

    def lookups(self, request, model_admin):
        return [(p.id, p.name) for p in Permission.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            permission_ids = self.value().split(",")
            return queryset.filter(extra_permissions__in=permission_ids).distinct()
        return queryset


class RolePermissionListFilter(admin.SimpleListFilter):
    title = 'Role Permissions'
    parameter_name = 'role_permissions'

    def lookups(self, request, model_admin):
        return [(p.id, p.name) for p in Permission.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            permission_ids = self.value().split(",")
            return queryset.filter(role__permissions__in=permission_ids).distinct()
        return queryset


# ---- Role Admin ----
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_permissions']
    search_fields = ['name']
    list_filter = [RolePermissionListFilter]   # multi-permission filter
    filter_horizontal = ['permissions']        # select multiple permissions

    def display_permissions(self, obj):
        return ", ".join([p.name for p in obj.permissions.all()])
    display_permissions.short_description = "Permissions"


# ---- CustomUser Admin ----
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Information', {
            'fields': (
                'first_name', 'last_name', 'name', 'email', 'phone', 'dob', 'gender',
                'primary_diagnosis', 'secondary_diagnosis', 'staff_id'
            )
        }),
        ('Address Information', {
            'fields': (
                'street', 'city', 'state', 'zip_code', 'country'
            )
        }),
        ('Parent/Guardian Information', {
            'fields': (
                'parent_name', 'parent_relationship', 'parent_phone', 
                'parent_email', 'prefered_contact_method'
            )
        }),
        ('Clinical Information', {
            'fields': (
                'assigned_bcba', 'assigned_rbt', 'preferred_session_time', 
                'preferred_session_duration', 'service_location', 'preferred_session_telehealth'
            )
        }),
        ('Business Information', {
            'fields': (
                'business_name', 'business_address', 'business_website'
            )
        }),
        ('Session Information', {
            'fields': (
                'session_duration', 'goals', 'session_focus', 'telehealth', 'session_note'
            )
        }),
        ('Emergency & Medical Information', {
            'fields': (
                'primary_physician', 'emergency_phone_number', 'allergies', 
                'medication', 'special_considerations'
            )
        }),
        ('Document Uploads', {
            'fields': (
                'consent_for_treatment', 'hippa_authorization', 'insurance_card', 
                'physician_referral', 'previous_assessment', 'iep'
            ),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
        ('Role & Tracking', {
            'fields': ('role', 'supervisor', 'status', 'extra_permissions')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2', 'role', 'status'
            ),
        }),
        ('Personal Information', {
            'classes': ('wide',),
            'fields': (
                'first_name', 'last_name', 'name', 'phone', 'dob', 'gender'
            ),
        }),
        ('Additional Information', {
            'classes': ('wide',),
            'fields': (
                'business_name', 'business_address', 'business_website',
                'supervisor', 'extra_permissions'
            ),
        }),
    )

    list_display = ("id", "name", "username", "email", "phone", "role", "status", "supervisor", 
                    "staff_id", "assigned_bcba", "assigned_rbt", "display_extra_permissions")
    search_fields = ("username", "email", "name", "phone", "staff_id", "role__name", 
                     "parent_name", "parent_email", "business_name")
    list_filter = ("role", "status", PermissionListFilter)  # filter by extra permissions
    filter_horizontal = ['extra_permissions']     # dual select box

    def display_extra_permissions(self, obj):
        return ", ".join([p.name for p in obj.extra_permissions.all()])
    display_extra_permissions.short_description = "Extra Permissions"

    def display_role_permissions(self, obj):
        if obj.role:
            return ", ".join([p.name for p in obj.role.permissions.all()])
        return "-"
    display_role_permissions.short_description = "Role Permissions"

admin.site.register(CustomUser, CustomUserAdmin)


# ---- Permission Admin ----
@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename']
    search_fields = ['name', 'codename']


# ---- User Role Assignment ----
@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'assigned_at']
    list_filter = ['role']


# ---- User Permission ----
@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'permission', 'assigned_at']
    list_filter = ['permission']


# ---- Certificate Admin ----
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'certificate_number', 'certificate_issue_date', 
                    'certificate_expiration_date', 'for_lifetime', 'created_at']
    list_filter = ['for_lifetime', 'created_at', 'certificate_issue_date', 'certificate_expiration_date']
    search_fields = ['user__username', 'user__email', 'name', 'certificate_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Certificate Details', {
            'fields': ('name', 'certificate_file', 'certificate_number', 
                      'certificate_issue_date', 'certificate_expiration_date', 'for_lifetime')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
