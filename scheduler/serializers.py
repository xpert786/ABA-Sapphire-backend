from rest_framework import serializers
from api.models import CustomUser
from .models import Session
import re

# Client serializer using CustomUser from API
class ClientSerializer(serializers.ModelSerializer):
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
            'id', 'username', 'name', 'email', 'role', 'phone',
            'business_name', 'business_address', 'business_website', 'status', 'goals', 'session_focus', 'telehealth', 'session_note'
        ]
        read_only_fields = ['id']

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
