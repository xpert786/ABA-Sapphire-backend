from rest_framework import serializers
from api.models import CustomUser
from .models import Session
from django.utils import timezone
from datetime import date
import re

# Client serializer using CustomUser from API
class ClientSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    last_session = serializers.SerializerMethodField()
    upcoming_session = serializers.SerializerMethodField()
    
    def get_age(self, obj):
        """Calculate age from date of birth"""
        if obj.dob:
            today = date.today()
            return today.year - obj.dob.year - ((today.month, today.day) < (obj.dob.month, obj.dob.day))
        return None
    
    def get_last_session(self, obj):
        """Get the most recent completed session for this client"""
        try:
            last_session = Session.objects.filter(
                client=obj,
                session_date__lt=timezone.now().date()
            ).order_by('-session_date', '-start_time').first()
            
            if last_session:
                return {
                    'id': last_session.id,
                    'session_date': last_session.session_date,
                    'start_time': last_session.start_time,
                    'end_time': last_session.end_time,
                    'staff_name': last_session.staff.name if last_session.staff else None,
                    'duration': str(last_session.duration) if last_session.duration else None,
                    'notes': last_session.session_notes
                }
        except Exception as e:
            pass
        return None
    
    def get_upcoming_session(self, obj):
        """Get the next upcoming session for this client"""
        try:
            upcoming_session = Session.objects.filter(
                client=obj,
                session_date__gte=timezone.now().date()
            ).order_by('session_date', 'start_time').first()
            
            if upcoming_session:
                return {
                    'id': upcoming_session.id,
                    'session_date': upcoming_session.session_date,
                    'start_time': upcoming_session.start_time,
                    'end_time': upcoming_session.end_time,
                    'staff_name': upcoming_session.staff.name if upcoming_session.staff else None,
                    'duration': str(upcoming_session.duration) if upcoming_session.duration else None
                }
        except Exception as e:
            pass
        return None
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Clean any problematic Unicode characters
        for key, value in data.items():
            if isinstance(value, str):
                # Remove or replace problematic characters
                data[key] = re.sub(r'[^\x00-\x7F]+', '?', value)
        return data
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'name', 'email', 'role', 'phone', 'dob',
            'business_name', 'business_address', 'business_website', 'status', 
            'goals', 'session_focus', 'telehealth', 'session_note',
            'age', 'last_session', 'upcoming_session'
        ]
        read_only_fields = ['id', 'age', 'last_session', 'upcoming_session']

# Staff serializer for nested representation
class StaffSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Clean any problematic Unicode characters
        for key, value in data.items():
            if isinstance(value, str):
                # Remove or replace problematic characters
                data[key] = re.sub(r'[^\x00-\x7F]+', '?', value)
        return data
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'name', 'email', 'phone', 'goals', 'session_focus', 'telehealth', 'session_note']
        read_only_fields = ['id']

# Session serializer
class SessionSerializer(serializers.ModelSerializer):
    staff_details = StaffSerializer(source='staff', read_only=True)
    client_details = ClientSerializer(source='client', read_only=True)
    
    def to_representation(self, instance):
        try:
            data = super().to_representation(instance)
            # Clean any problematic Unicode characters
            for key, value in data.items():
                if isinstance(value, str):
                    # Remove or replace problematic characters
                    data[key] = re.sub(r'[^\x00-\x7F]+', '?', value)
            return data
        except UnicodeEncodeError as e:
            # If there's still a Unicode error, return minimal safe data
            return {
                'id': instance.id,
                'session_date': str(instance.session_date) if instance.session_date else None,
                'start_time': str(instance.start_time) if instance.start_time else None,
                'end_time': str(instance.end_time) if instance.end_time else None,
                'error': 'Unicode encoding issue with this record'
            }
    
    class Meta:
        model = Session
        fields = '__all__'

    def validate(self, data):
        staff = data.get('staff')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        # Optional: Check for overlapping sessions (commented out to allow overlaps)
        # overlapping = Session.objects.filter(
        #     staff=staff,
        #     start_time__lt=end_time,
        #     end_time__gt=start_time
        # )
        # if self.instance:
        #     overlapping = overlapping.exclude(id=self.instance.id)

        # if overlapping.exists():
        #     raise serializers.ValidationError("Staff has overlapping session at this time.")
        return data
