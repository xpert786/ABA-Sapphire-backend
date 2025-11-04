from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from .models import TreatmentPlan, TreatmentGoal, TreatmentPlanApproval
from .serializers import (
    TreatmentPlanSerializer, TreatmentPlanListSerializer, TreatmentPlanCreateSerializer,
    TreatmentGoalSerializer, TreatmentPlanApprovalSerializer
)

class TreatmentPlanListCreateView(generics.ListCreateAPIView):
    """List all treatment plans or create a new one"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TreatmentPlanCreateSerializer
        return TreatmentPlanListSerializer
    
    def get_queryset(self):
        queryset = TreatmentPlan.objects.select_related('bcba').prefetch_related('goals')
        
        # Role-based access control
        if self.request.user.is_staff:
            # Admin can see all treatment plans
            pass
        else:
            # Regular users can only see their own treatment plans
            queryset = queryset.filter(bcba=self.request.user)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority if provided
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        # Filter by plan type if provided
        plan_type_filter = self.request.query_params.get('plan_type')
        if plan_type_filter:
            queryset = queryset.filter(plan_type=plan_type_filter)
        
        # Search by client name or ID
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(client_name__icontains=search) | Q(client_id__icontains=search)
            )
        
        return queryset.order_by('-created_at')

class TreatmentPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a treatment plan"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TreatmentPlanSerializer
    
    def get_queryset(self):
        queryset = TreatmentPlan.objects.select_related('bcba').prefetch_related('goals')
        
        # Filter by BCBA if user is not admin
        if not self.request.user.is_staff:
            queryset = queryset.filter(bcba=self.request.user)
        
        return queryset

class TreatmentGoalListCreateView(generics.ListCreateAPIView):
    """List goals for a treatment plan or create a new goal"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TreatmentGoalSerializer
    
    def get_queryset(self):
        treatment_plan_id = self.kwargs['treatment_plan_id']
        treatment_plan = get_object_or_404(TreatmentPlan, id=treatment_plan_id)
        
        # Check if user has permission to view this treatment plan
        if not self.request.user.is_staff and treatment_plan.bcba != self.request.user:
            return TreatmentGoal.objects.none()
        
        return TreatmentGoal.objects.filter(treatment_plan=treatment_plan).order_by('priority', 'created_at')
    
    def perform_create(self, serializer):
        treatment_plan_id = self.kwargs['treatment_plan_id']
        treatment_plan = get_object_or_404(TreatmentPlan, id=treatment_plan_id)
        
        # Check if user has permission to modify this treatment plan
        if not self.request.user.is_staff and treatment_plan.bcba != self.request.user:
            raise permissions.PermissionDenied("You don't have permission to add goals to this treatment plan.")
        
        serializer.save(treatment_plan=treatment_plan)

class TreatmentGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a treatment goal"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TreatmentGoalSerializer
    
    def get_queryset(self):
        treatment_plan_id = self.kwargs['treatment_plan_id']
        treatment_plan = get_object_or_404(TreatmentPlan, id=treatment_plan_id)
        
        # Check if user has permission to view this treatment plan
        if not self.request.user.is_staff and treatment_plan.bcba != self.request.user:
            return TreatmentGoal.objects.none()
        
        return TreatmentGoal.objects.filter(treatment_plan=treatment_plan)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_treatment_plan(request, pk):
    """Submit a treatment plan for approval"""
    treatment_plan = get_object_or_404(TreatmentPlan, pk=pk)
    
    # Check if user has permission to submit this treatment plan
    if not request.user.is_staff and treatment_plan.bcba != request.user:
        return Response(
            {'error': "You don't have permission to submit this treatment plan."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if treatment_plan.status != 'draft':
        return Response(
            {'error': 'Only draft treatment plans can be submitted for approval.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    treatment_plan.status = 'submitted'
    treatment_plan.submitted_at = timezone.now()
    treatment_plan.save()
    
    return Response(
        {'message': 'Treatment plan submitted for approval successfully.'},
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_treatment_plan(request, pk):
    """Approve or reject a treatment plan (admin only)"""
    if not request.user.is_staff:
        return Response(
            {'error': 'Only administrators can approve treatment plans.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    treatment_plan = get_object_or_404(TreatmentPlan, pk=pk)
    
    if treatment_plan.status != 'submitted':
        return Response(
            {'error': 'Only submitted treatment plans can be approved.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    approved = request.data.get('approved', True)
    approval_notes = request.data.get('approval_notes', '')
    
    # Update treatment plan status
    treatment_plan.status = 'approved' if approved else 'rejected'
    if approved:
        treatment_plan.approved_at = timezone.now()
    treatment_plan.save()
    
    # Create approval record
    TreatmentPlanApproval.objects.create(
        treatment_plan=treatment_plan,
        approver=request.user,
        approved=approved,
        approval_notes=approval_notes
    )
    
    status_message = 'approved' if approved else 'rejected'
    return Response(
        {'message': f'Treatment plan {status_message} successfully.'},
        status=status.HTTP_200_OK
    )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def treatment_plan_stats(request):
    """Get statistics for treatment plans"""
    if not request.user.is_staff:
        queryset = TreatmentPlan.objects.filter(bcba=request.user)
    else:
        queryset = TreatmentPlan.objects.all()
    
    stats = {
        'total_plans': queryset.count(),
        'draft_plans': queryset.filter(status='draft').count(),
        'submitted_plans': queryset.filter(status='submitted').count(),
        'approved_plans': queryset.filter(status='approved').count(),
        'rejected_plans': queryset.filter(status='rejected').count(),
        'high_priority_plans': queryset.filter(priority='high').count(),
        'medium_priority_plans': queryset.filter(priority='medium').count(),
        'low_priority_plans': queryset.filter(priority='low').count(),
    }
    
    return Response(stats, status=status.HTTP_200_OK)

class TreatmentPlanApprovalListView(generics.ListAPIView):
    """List treatment plan approvals (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TreatmentPlanApprovalSerializer
    
    def get_queryset(self):
        if not self.request.user.is_staff:
            return TreatmentPlanApproval.objects.none()
        
        return TreatmentPlanApproval.objects.select_related(
            'treatment_plan', 'approver'
        ).order_by('-approved_at')

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_client_from_treatment_plan(request, pk):
    """
    Get the matched client user information for a treatment plan.
    This endpoint helps you find the client ID before creating a session.
    
    Returns the client user that would be automatically selected when 
    creating a session with this treatment_plan_id.
    
    Endpoint: GET /sapphire/treatment-plan/plans/{pk}/client/
    """
    try:
        from django.contrib.auth import get_user_model
        CustomUser = get_user_model()
        
        treatment_plan = get_object_or_404(TreatmentPlan, id=pk)
        
        # Find the client user using the same logic as in the serializer
        client_user = None
        client_id_str = str(treatment_plan.client_id)
        matching_methods = []
        
        # Try to find by username
        try:
            client_user = CustomUser.objects.get(username=client_id_str, role__name='Clients/Parent')
            matching_methods.append('username')
        except CustomUser.DoesNotExist:
            pass
        
        # Try to find by staff_id if not found
        if not client_user:
            try:
                client_user = CustomUser.objects.get(staff_id=client_id_str, role__name='Clients/Parent')
                matching_methods.append('staff_id')
            except CustomUser.DoesNotExist:
                pass
        
        # Try to find by id if client_id is numeric
        if not client_user and client_id_str.isdigit():
            try:
                client_user = CustomUser.objects.get(id=int(client_id_str), role__name='Clients/Parent')
                matching_methods.append('id')
            except (CustomUser.DoesNotExist, ValueError):
                pass
        
        # Try to find by name (partial match)
        if not client_user:
            try:
                client_user = CustomUser.objects.filter(
                    name__icontains=treatment_plan.client_name,
                    role__name='Clients/Parent'
                ).first()
                if client_user:
                    matching_methods.append('name (partial)')
            except Exception:
                pass
        
        if client_user:
            return Response({
                'treatment_plan': {
                    'id': treatment_plan.id,
                    'client_name': treatment_plan.client_name,
                    'client_id': treatment_plan.client_id,
                    'plan_type': treatment_plan.get_plan_type_display() if hasattr(treatment_plan, 'get_plan_type_display') else treatment_plan.plan_type
                },
                'matched_client': {
                    'id': client_user.id,
                    'username': client_user.username,
                    'name': client_user.name or client_user.get_full_name() or client_user.username,
                    'email': client_user.email,
                    'staff_id': client_user.staff_id,
                    'role': client_user.role.name if client_user.role else None
                },
                'matching_method': matching_methods[0] if matching_methods else 'unknown',
                'message': f'Client found! Use client ID {client_user.id} or simply use treatment_plan_id when creating a session.'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'treatment_plan': {
                    'id': treatment_plan.id,
                    'client_name': treatment_plan.client_name,
                    'client_id': treatment_plan.client_id
                },
                'matched_client': None,
                'error': f'Could not find a client user matching treatment plan client_id "{treatment_plan.client_id}" or client_name "{treatment_plan.client_name}".',
                'suggestion': 'Please create the client user first or verify the client_id/client_name in the treatment plan matches an existing user.'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response({
            'error': f'Error retrieving client information: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def ai_goal_suggestions(request):
    """
    AI-powered goal suggestions for treatment plan creation.
    
    Accepts treatment plan data and returns AI-generated goal suggestions.
    Can be used during plan creation or editing.
    
    Request body can include:
    - client_name (required)
    - client_id (optional)
    - plan_type (required)
    - assessment_tools_used (optional)
    - client_strengths (optional)
    - areas_of_need (required for better suggestions)
    - existing_goals (optional) - to avoid suggesting duplicates
    
    Returns structured goal suggestions with mastery criteria recommendations.
    """
    # Check if user is BCBA, Admin, or Superadmin
    user = request.user
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        if role_name not in ['BCBA', 'Admin', 'Superadmin']:
            return Response({
                'error': 'Only BCBAs, Admins, and Superadmins can generate goal suggestions'
            }, status=status.HTTP_403_FORBIDDEN)
    
    # Get treatment plan data from request
    request_data = request.data
    
    # Extract plan information
    client_name = request_data.get('client_name', '')
    client_id = request_data.get('client_id', '')
    plan_type = request_data.get('plan_type', 'comprehensive_aba')
    assessment_tools_used = request_data.get('assessment_tools_used', '')
    client_strengths = request_data.get('client_strengths', '')
    areas_of_need = request_data.get('areas_of_need', '')
    existing_goals = request_data.get('existing_goals', [])  # List of existing goal descriptions
    
    # Validate required fields
    if not client_name or not plan_type:
        return Response({
            'error': 'client_name and plan_type are required fields'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get available mastery criteria options from the model
    mastery_criteria_options = [choice[0] for choice in TreatmentGoal.MASTERY_CRITERIA_CHOICES]
    
    # Build comprehensive prompt for OpenAI
    prompt = f"""You are an expert Board Certified Behavior Analyst (BCBA) creating ABA treatment goals.

TREATMENT PLAN CONTEXT:
- Client Name: {client_name}
- Plan Type: {plan_type}
- Assessment Tools: {assessment_tools_used if assessment_tools_used else 'Not specified'}
- Client Strengths: {client_strengths if client_strengths else 'To be determined'}
- Areas of Need: {areas_of_need if areas_of_need else 'General ABA support needed'}

{'EXISTING GOALS (avoid duplicating these):' + ', '.join([g.get('goal_description', g) if isinstance(g, dict) else str(g) for g in existing_goals]) if existing_goals else ''}

TASK:
Generate 5-8 specific, measurable, and appropriate ABA treatment goals for this client based on the plan type and areas of need.

For each goal, provide:
1. A clear, specific goal description (what the client will achieve)
2. A recommended mastery_criteria from this list: {', '.join(mastery_criteria_options[:10])}...
3. Priority level (high, medium, or low)
4. Brief rationale for why this goal is appropriate

AVAILABLE MASTERY CRITERIA OPTIONS:
{', '.join(mastery_criteria_options)}

Plan Type Guidelines:
- comprehensive_aba: Broad goals covering multiple skill areas
- behavior_reduction_focus: Goals targeting specific behaviors to reduce
- social_skills_development: Goals focused on social interaction and communication
- communication_language: Goals for language and communication skills
- early_intervention: Developmentally appropriate goals for young children
- school_based_support: Goals aligned with educational settings
- parent_training_focus: Goals involving parent/caregiver training
- transition_planning: Goals for transitions and independence

Return the goals in JSON format with this structure:
{{
    "goals": [
        {{
            "goal_description": "Specific goal description here",
            "mastery_criteria": "80%_accuracy",
            "priority": "high",
            "rationale": "Brief explanation of why this goal is appropriate"
        }}
    ]
}}

Ensure goals are:
- Specific and measurable
- Appropriate for the plan type
- Not duplicating existing goals
- Using valid mastery_criteria values
- Prioritized based on client needs"""
    
    # Call OpenAI API
    try:
        from openai import OpenAI
        from django.conf import settings
        
        client = OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', None))
        
        if not client.api_key:
            return Response({
                'error': 'OpenAI API key not configured',
                'message': 'Please configure OPENAI_API_KEY in settings'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert BCBA assistant. Always return valid JSON with the exact structure requested. Use only the mastery_criteria values provided."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        import json
        import re
        
        # Try to extract JSON from the response (AI might add markdown formatting)
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            ai_response = json_match.group(0)
        
        suggestions_data = json.loads(ai_response)
        
        # Validate and format suggestions
        validated_goals = []
        for goal in suggestions_data.get('goals', []):
            # Validate mastery_criteria
            mastery_criteria = goal.get('mastery_criteria', '80%_accuracy')
            if mastery_criteria not in mastery_criteria_options:
                mastery_criteria = '80%_accuracy'  # Default fallback
            
            validated_goal = {
                'goal_description': goal.get('goal_description', ''),
                'mastery_criteria': mastery_criteria,
                'priority': goal.get('priority', 'medium'),
                'rationale': goal.get('rationale', ''),
                'suggested_custom_mastery_criteria': goal.get('custom_mastery_criteria', '') if mastery_criteria == 'custom' else None
            }
            validated_goals.append(validated_goal)
        
        return Response({
            'suggestions': validated_goals,
            'total_suggestions': len(validated_goals),
            'plan_context': {
                'client_name': client_name,
                'plan_type': plan_type,
                'areas_of_need': areas_of_need
            },
            'message': f'Generated {len(validated_goals)} goal suggestions based on treatment plan data'
        }, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError as e:
        return Response({
            'error': 'Failed to parse AI response as JSON',
            'raw_response': ai_response[:500] if 'ai_response' in locals() else 'No response',
            'message': 'The AI response could not be parsed. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'error': f'Error generating goal suggestions: {str(e)}',
            'message': 'Please check your OpenAI API key and try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ai_goal_suggestions_for_plan(request, pk):
    """
    Get AI goal suggestions for an existing treatment plan.
    
    Uses the treatment plan's data to generate goal suggestions.
    Endpoint: GET /sapphire/treatment-plan/plans/<plan_id>/goal-suggestions/
    """
    # Check if user is BCBA, Admin, or Superadmin
    user = request.user
    if hasattr(user, 'role') and user.role:
        role_name = user.role.name if hasattr(user.role, 'name') else str(user.role)
        if role_name not in ['BCBA', 'Admin', 'Superadmin']:
            return Response({
                'error': 'Only BCBAs, Admins, and Superadmins can generate goal suggestions'
            }, status=status.HTTP_403_FORBIDDEN)
    
    # Get the treatment plan
    try:
        treatment_plan = TreatmentPlan.objects.select_related('bcba').prefetch_related('goals').get(pk=pk)
    except TreatmentPlan.DoesNotExist:
        return Response({
            'error': 'Treatment plan not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check permissions
    if not user.is_staff and treatment_plan.bcba != user:
        return Response({
            'error': 'You can only generate suggestions for your own treatment plans'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get existing goals
    existing_goals = list(treatment_plan.goals.values_list('goal_description', flat=True))
    
    # Prepare request data for the AI suggestion function
    request_data = {
        'client_name': treatment_plan.client_name,
        'client_id': treatment_plan.client_id,
        'plan_type': treatment_plan.plan_type,
        'assessment_tools_used': treatment_plan.assessment_tools_used or '',
        'client_strengths': treatment_plan.client_strengths or '',
        'areas_of_need': treatment_plan.areas_of_need or '',
        'existing_goals': existing_goals
    }
    
    # Create a mock request object to pass to the AI function
    class MockRequest:
        def __init__(self, data, user):
            self.data = data
            self.user = user
    
    mock_request = MockRequest(request_data, user)
    
    # Call the AI suggestion function
    return ai_goal_suggestions(mock_request)