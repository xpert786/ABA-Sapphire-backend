from rest_framework import serializers
from django.utils import timezone
from .models import ChatMessage, Alert, SessionPrompt, SessionNoteFlow, SkillProgress, Milestone, ProgressMonitoring, AIResponse


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'   # or list specific fields if you want
    def get_created_at_local(self, obj):
        return timezone.localtime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S")

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'

class SessionPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionPrompt
        fields = '__all__'

class SessionNoteFlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionNoteFlow
        fields = '__all__'

class MilestoneSerializer(serializers.ModelSerializer):
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    
    class Meta:
        model = Milestone
        fields = '__all__'
        read_only_fields = ['created_at', 'verified_at']

class SkillProgressSerializer(serializers.ModelSerializer):
    milestones = MilestoneSerializer(many=True, read_only=True)
    milestones_count = serializers.SerializerMethodField()
    client_name = serializers.CharField(source='client.name', read_only=True)
    treatment_plan_name = serializers.CharField(source='treatment_plan.client_name', read_only=True)
    
    class Meta:
        model = SkillProgress
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_milestones_count(self, obj):
        return obj.milestones.count()

class ProgressMonitoringSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    client_id = serializers.CharField(source='client.id', read_only=True)
    treatment_plan_id = serializers.IntegerField(source='treatment_plan.id', read_only=True)
    treatment_plan_name = serializers.CharField(source='treatment_plan.client_name', read_only=True)
    
    class Meta:
        model = ProgressMonitoring
        fields = '__all__'
        read_only_fields = ['calculated_at', 'updated_at']

class AIResponseSerializer(serializers.ModelSerializer):
    """Serializer for AI Response model"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    session_id = serializers.IntegerField(source='session.id', read_only=True)
    session_date = serializers.DateField(source='session.session_date', read_only=True)
    response_type_display = serializers.CharField(source='get_response_type_display', read_only=True)
    
    class Meta:
        model = AIResponse
        fields = [
            'id', 'response_type', 'response_type_display', 'user', 'user_name', 'user_username',
            'session', 'session_id', 'session_date', 'prompt', 'response', 'context_data',
            'model_used', 'tokens_used', 'processing_time', 'is_successful', 'error_message',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        # Set user from request if not provided
        if 'user' not in validated_data:
            validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Prevent updating certain fields
        validated_data.pop('user', None)  # Don't allow changing user
        validated_data.pop('created_at', None)  # Don't allow changing created_at
        return super().update(instance, validated_data)
