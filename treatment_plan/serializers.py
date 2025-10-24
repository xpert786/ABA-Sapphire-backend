from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import TreatmentPlan, TreatmentGoal, TreatmentPlanApproval

User = get_user_model()

class TreatmentGoalSerializer(serializers.ModelSerializer):
    """Serializer for treatment goals"""
    
    class Meta:
        model = TreatmentGoal
        fields = [
            'id', 'goal_description', 'mastery_criteria', 'custom_mastery_criteria',
            'priority', 'is_achieved', 'achieved_date', 'progress_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'achieved_date']

class TreatmentPlanSerializer(serializers.ModelSerializer):
    """Serializer for treatment plans"""
    goals = TreatmentGoalSerializer(many=True, required=False)
    bcba_name = serializers.CharField(source='bcba.get_full_name', read_only=True)
    bcba_email = serializers.CharField(source='bcba.email', read_only=True)
    goals_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TreatmentPlan
        fields = [
            'id', 'client_name', 'client_id', 'bcba', 'bcba_name', 'bcba_email',
            'assessment_tools_used', 'client_strengths', 'areas_of_need',
            'reinforcement_strategies', 'prompting_hierarchy', 'behavior_interventions',
            'data_collection_methods', 'status', 'priority',
            'created_at', 'updated_at', 'submitted_at', 'approved_at',
            'goals', 'goals_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'submitted_at', 'approved_at']
    
    def get_goals_count(self, obj):
        return obj.goals.count()
    
    def create(self, validated_data):
        goals_data = validated_data.pop('goals', [])
        treatment_plan = TreatmentPlan.objects.create(**validated_data)
        
        for goal_data in goals_data:
            TreatmentGoal.objects.create(treatment_plan=treatment_plan, **goal_data)
        
        return treatment_plan
    
    def update(self, instance, validated_data):
        goals_data = validated_data.pop('goals', None)
        
        # Update treatment plan fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update goals if provided
        if goals_data is not None:
            # Delete existing goals
            instance.goals.all().delete()
            # Create new goals
            for goal_data in goals_data:
                TreatmentGoal.objects.create(treatment_plan=instance, **goal_data)
        
        return instance

class TreatmentPlanListSerializer(serializers.ModelSerializer):
    """Simplified serializer for treatment plan lists"""
    bcba_name = serializers.CharField(source='bcba.get_full_name', read_only=True)
    goals_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TreatmentPlan
        fields = [
            'id', 'client_name', 'client_id', 'bcba_name', 'status', 'priority',
            'created_at', 'goals_count'
        ]
    
    def get_goals_count(self, obj):
        return obj.goals.count()

class TreatmentPlanApprovalSerializer(serializers.ModelSerializer):
    """Serializer for treatment plan approvals"""
    approver_name = serializers.CharField(source='approver.get_full_name', read_only=True)
    treatment_plan_info = TreatmentPlanListSerializer(source='treatment_plan', read_only=True)
    
    class Meta:
        model = TreatmentPlanApproval
        fields = [
            'id', 'treatment_plan', 'treatment_plan_info', 'approver', 'approver_name',
            'approved', 'approval_notes', 'approved_at'
        ]
        read_only_fields = ['id', 'approved_at']

class TreatmentPlanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating treatment plans with goals"""
    goals = TreatmentGoalSerializer(many=True, required=False)
    
    class Meta:
        model = TreatmentPlan
        fields = [
            'client_name', 'client_id', 'bcba',
            'assessment_tools_used', 'client_strengths', 'areas_of_need',
            'reinforcement_strategies', 'prompting_hierarchy', 'behavior_interventions',
            'data_collection_methods', 'priority', 'goals'
        ]
    
    def create(self, validated_data):
        goals_data = validated_data.pop('goals', [])
        treatment_plan = TreatmentPlan.objects.create(**validated_data)
        
        for goal_data in goals_data:
            TreatmentGoal.objects.create(treatment_plan=treatment_plan, **goal_data)
        
        return treatment_plan
