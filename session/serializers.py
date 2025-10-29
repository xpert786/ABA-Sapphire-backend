from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Session, SessionTimer, AdditionalTime, PreSessionChecklist,
    Activity, ReinforcementStrategy, ABCEvent, GoalProgress,
    Incident, SessionNote, TimeTracker
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'name']

class SessionTimerSerializer(serializers.ModelSerializer):
    """Serializer for SessionTimer"""
    current_duration = serializers.ReadOnlyField()
    
    class Meta:
        model = SessionTimer
        fields = ['id', 'start_time', 'end_time', 'is_running', 'total_duration', 'current_duration']

class AdditionalTimeSerializer(serializers.ModelSerializer):
    """Serializer for AdditionalTime"""
    class Meta:
        model = AdditionalTime
        fields = ['id', 'time_type', 'duration', 'unit', 'reason', 'added_at']

class PreSessionChecklistSerializer(serializers.ModelSerializer):
    """Serializer for PreSessionChecklist"""
    class Meta:
        model = PreSessionChecklist
        fields = ['id', 'item_name', 'is_completed', 'notes']

class ActivitySerializer(serializers.ModelSerializer):
    """Serializer for Activity"""
    class Meta:
        model = Activity
        fields = ['id', 'activity_name', 'duration_minutes', 'reinforcement_strategies', 'notes']

class ReinforcementStrategySerializer(serializers.ModelSerializer):
    """Serializer for ReinforcementStrategy"""
    class Meta:
        model = ReinforcementStrategy
        fields = ['id', 'strategy_type', 'frequency', 'pr_ratio', 'notes']

class ABCEventSerializer(serializers.ModelSerializer):
    """Serializer for ABCEvent"""
    class Meta:
        model = ABCEvent
        fields = ['id', 'antecedent', 'behavior', 'consequence', 'timestamp']

class GoalProgressSerializer(serializers.ModelSerializer):
    """Serializer for GoalProgress"""
    class Meta:
        model = GoalProgress
        fields = ['id', 'goal_description', 'is_met', 'implementation_method', 'notes']

class IncidentSerializer(serializers.ModelSerializer):
    """Serializer for Incident"""
    class Meta:
        model = Incident
        fields = ['id', 'incident_type', 'behavior_severity', 'start_time', 'duration_minutes', 'description', 'created_at']

class SessionNoteSerializer(serializers.ModelSerializer):
    """Serializer for SessionNote"""
    class Meta:
        model = SessionNote
        fields = ['id', 'note_content', 'note_type', 'created_at']

class TimeTrackerSerializer(serializers.ModelSerializer):
    """Serializer for TimeTracker model"""
    duration = serializers.ReadOnlyField()
    duration_display = serializers.ReadOnlyField()
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = TimeTracker
        fields = [
            'id', 'session', 'time_type', 'start_time', 'end_time',
            'description', 'created_by', 'duration', 'duration_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate that end_time is after start_time"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError("End time must be after start time")
        
        return data

class SessionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for session lists"""
    client = UserSerializer(read_only=True)
    staff = UserSerializer(read_only=True)
    
    class Meta:
        model = Session
        fields = [
            'id', 'client', 'staff', 'session_date', 'start_time', 'end_time',
            'status', 'location', 'service_type', 'created_at'
        ]

class SessionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for session with all related data"""
    client = UserSerializer(read_only=True)
    staff = UserSerializer(read_only=True)
    timer = SessionTimerSerializer(read_only=True)
    additional_times = AdditionalTimeSerializer(many=True, read_only=True)
    checklist_items = PreSessionChecklistSerializer(many=True, read_only=True)
    activities = ActivitySerializer(many=True, read_only=True)
    reinforcement_strategies = ReinforcementStrategySerializer(many=True, read_only=True)
    abc_events = ABCEventSerializer(many=True, read_only=True)
    goal_progress = GoalProgressSerializer(many=True, read_only=True)
    incidents = IncidentSerializer(many=True, read_only=True)
    notes = SessionNoteSerializer(many=True, read_only=True)
    time_trackers = TimeTrackerSerializer(many=True, read_only=True)
    
    class Meta:
        model = Session
        fields = [
            'id', 'client', 'staff', 'session_date', 'start_time', 'end_time',
            'status', 'session_notes', 'duration', 'location', 'service_type',
            'created_at', 'updated_at', 'timer', 'additional_times', 'checklist_items',
            'activities', 'reinforcement_strategies', 'abc_events', 'goal_progress',
            'incidents', 'notes', 'time_trackers'
        ]

class SessionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating sessions"""
    class Meta:
        model = Session
        fields = [
            'client', 'staff', 'session_date', 'start_time', 'end_time',
            'status', 'session_notes', 'location', 'service_type'
        ]

    def validate(self, data):
        """Validate session data"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("End time must be after start time")
        
        return data

class SessionTimerStartStopSerializer(serializers.Serializer):
    """Serializer for starting/stopping session timer"""
    action = serializers.ChoiceField(choices=['start', 'stop'])
    
    def validate_action(self, value):
        if value not in ['start', 'stop']:
            raise serializers.ValidationError("Action must be 'start' or 'stop'")
        return value

class SessionSubmitSerializer(serializers.Serializer):
    """Serializer for submitting session data"""
    session_id = serializers.IntegerField()
    submit_type = serializers.ChoiceField(choices=['draft', 'submit'])
    
    def validate_session_id(self, value):
        try:
            Session.objects.get(id=value)
        except Session.DoesNotExist:
            raise serializers.ValidationError("Session not found")
        return value

class SessionPreviewSerializer(serializers.Serializer):
    """Serializer for session preview data"""
    session_id = serializers.IntegerField()
    
    def validate_session_id(self, value):
        try:
            Session.objects.get(id=value)
        except Session.DoesNotExist:
            raise serializers.ValidationError("Session not found")
        return value

class TimeTrackerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating TimeTracker entries"""
    
    class Meta:
        model = TimeTracker
        fields = ['session', 'time_type', 'start_time', 'end_time', 'description']

    def validate(self, data):
        """Validate that end_time is after start_time"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError("End time must be after start time")
        
        return data

    def create(self, validated_data):
        """Create a new TimeTracker entry"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class TimeTrackerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating TimeTracker entries"""
    
    class Meta:
        model = TimeTracker
        fields = ['time_type', 'start_time', 'end_time', 'description']

    def validate(self, data):
        """Validate that end_time is after start_time"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError("End time must be after start time")
        
        return data
