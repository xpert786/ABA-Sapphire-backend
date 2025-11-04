from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import ChatMessageSerializer, AlertSerializer
import openai
from django.conf import settings
from django.utils import timezone

def broadcast_chat(chat):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{chat.user.id}",
        {"type": "chat_message", "message": ChatMessageSerializer(chat).data}
    )

def broadcast_alert(alert):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{alert.user.id}",
        {"type": "alert_message", "message": AlertSerializer(alert).data}
    )


def generate_ai_response(prompt: str, context: str = "") -> str:
    """
    Generate AI response using GPT-4, with optional context for up-to-date info.
    """
    openai.api_key = settings.OPENAI_API_KEY

    if not openai.api_key:
        return "AI error: API key not set"

    try:
        messages = [
            {"role": "system", "content": "You are a factual assistant. Use the context if provided to answer accurately."}
        ]

        if context:
            messages.append({"role": "user", "content": f"Context: {context}"})

        messages.append({"role": "user", "content": prompt})

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=150,
            temperature=0  # factual, no guessing
        )

        ai_text = response.choices[0].message.content
        return ai_text

    except Exception as e:
        return f"AI error: {e}"


def generate_ai_response_with_db_context(prompt: str, user) -> str:
    """
    Generate AI response using GPT-4 with database context based on authenticated user.
    For admin users, includes comprehensive business overview data.
    """
    openai.api_key = settings.OPENAI_API_KEY

    if not openai.api_key:
        return "AI error: API key not set"

    try:
        # Gather user-specific context from database
        context = build_user_context(user)
        
        # Determine role-specific instructions
        role_name = user.role.name if user.role else None
        
        if role_name in ['Admin', 'Superadmin']:
            system_prompt = f"""You are Ocean AI, an intelligent business assistant for a healthcare/ABA therapy management system.
            
You have access to comprehensive business overview data including:
- User statistics (total users, active users, clients, staff)
- Session statistics (total sessions, completed, upcoming, attendance rates)
- Goal statistics (total goals, achievement rates)
- Treatment plan statistics (total plans, approved plans, goals)
- Incident statistics
- Staff productivity metrics
- Client progress data

USER CONTEXT:
{context}

CAPABILITIES:
- Provide business insights and analytics based on the data
- Answer questions about KPIs, performance metrics, and trends
- Give recommendations based on business data
- Help with administrative decision-making
- All data shown is filtered based on user's supervisory scope (if applicable)

IMPORTANT:
- Use specific numbers and percentages from the context
- Provide actionable insights when possible
- For business questions, reference the business overview data
- Be professional, data-driven, and helpful"""
        else:
            system_prompt = f"""You are Ocean AI, an intelligent assistant for a healthcare/ABA therapy management system.
            
You have access to the following user-specific context:
{context}

CAPABILITIES:
- Answer questions about the user's sessions, goals, and progress
- Provide information about upcoming sessions and assignments
- Help with therapy-related questions
- All information shown is specific to this user's involvement

IMPORTANT:
- Use specific information from the context
- Be professional and supportive
- Focus on the user's own data and experiences"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        # Increase token limit for business overview responses
        max_tokens = 500 if role_name in ['Admin', 'Superadmin'] else 300

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3  # Slightly more creative but still factual
        )

        ai_text = response.choices[0].message.content
        return ai_text

    except Exception as e:
        return f"AI error: {e}"


def build_user_context(user):
    """
    Build context string from user's database information.
    Includes comprehensive data filtered by user involvement.
    """
    from api.models import CustomUser
    from scheduler.models import Session as SchedulerSession
    from session.models import Session as TherapySession, GoalProgress, Incident
    from treatment_plan.models import TreatmentPlan, TreatmentGoal
    from django.db.models import Count, Q, Avg
    from datetime import timedelta
    
    context_parts = []
    
    # Basic user info
    context_parts.append(f"User: {user.name or user.username} ({user.username})")
    context_parts.append(f"Role: {user.role.name if user.role else 'No role assigned'}")
    context_parts.append(f"Email: {user.email}")
    context_parts.append(f"Status: {user.status}")
    
    # Supervisor info
    if user.supervisor:
        context_parts.append(f"Supervisor: {user.supervisor.name} ({user.supervisor.role.name if user.supervisor.role else 'No role'})")
    
    # Role-specific context
    if user.role:
        role_name = user.role.name
        
        if role_name == 'RBT':
            # RBT specific info - only data where user is involved
            context_parts.append(f"Staff ID: {user.staff_id}")
            if user.assigned_bcba:
                context_parts.append(f"Assigned BCBA: {user.assigned_bcba.name}")
            
            # Get sessions where RBT is assigned
            my_sessions = TherapySession.objects.filter(staff=user)
            total_sessions = my_sessions.count()
            completed_sessions = my_sessions.filter(status='completed').count()
            upcoming_sessions = my_sessions.filter(
                session_date__gte=timezone.now().date(),
                status__in=['scheduled', 'in_progress']
            ).order_by('session_date', 'start_time')[:5]
            
            context_parts.append(f"Total Sessions: {total_sessions} (Completed: {completed_sessions})")
            
            if upcoming_sessions:
                context_parts.append("Upcoming sessions:")
                for session in upcoming_sessions:
                    context_parts.append(f"- {session.session_date} at {session.start_time} with {session.client.name or session.client.username}")
            
            # Get clients assigned to this RBT
            my_clients = CustomUser.objects.filter(assigned_rbt=user)
            if my_clients:
                context_parts.append(f"Assigned Clients: {my_clients.count()}")
                for client in my_clients[:5]:
                    context_parts.append(f"- {client.name or client.username}")
            
        elif role_name == 'BCBA':
            # BCBA specific info - only data where user is involved
            context_parts.append(f"Staff ID: {user.staff_id}")
            
            # Get supervised RBTs
            supervised_rbts = CustomUser.objects.filter(assigned_bcba=user)
            if supervised_rbts:
                context_parts.append(f"Supervised RBTs: {supervised_rbts.count()}")
                for rbt in supervised_rbts[:5]:
                    context_parts.append(f"- {rbt.name or rbt.username} ({rbt.staff_id})")
            
            # Get treatment plans created by this BCBA
            my_plans = TreatmentPlan.objects.filter(bcba=user)
            context_parts.append(f"Treatment Plans Created: {my_plans.count()}")
            
            # Get sessions where BCBA is assigned or supervises
            my_sessions = TherapySession.objects.filter(
                Q(staff=user) | Q(client__assigned_bcba=user)
            )
            context_parts.append(f"Related Sessions: {my_sessions.count()}")
            
        elif role_name == 'Clients/Parent':
            # Client specific info - only their own data
            context_parts.append(f"Client ID: {user.staff_id}")
            if user.assigned_rbt:
                context_parts.append(f"Assigned RBT: {user.assigned_rbt.name}")
            if user.assigned_bcba:
                context_parts.append(f"Assigned BCBA: {user.assigned_bcba.name}")
            
            # Get sessions for this client
            my_sessions = TherapySession.objects.filter(client=user)
            total_sessions = my_sessions.count()
            completed_sessions = my_sessions.filter(status='completed').count()
            upcoming_sessions = my_sessions.filter(
                session_date__gte=timezone.now().date(),
                status__in=['scheduled', 'in_progress']
            ).order_by('session_date', 'start_time')[:5]
            
            context_parts.append(f"Total Sessions: {total_sessions} (Completed: {completed_sessions})")
            
            if upcoming_sessions:
                context_parts.append("Upcoming sessions:")
                for session in upcoming_sessions:
                    context_parts.append(f"- {session.session_date} at {session.start_time} with {session.staff.name if session.staff else 'TBD'}")
            
            # Get treatment plans for this client
            my_plans = TreatmentPlan.objects.filter(client_id=str(user.id))
            if my_plans:
                context_parts.append(f"Treatment Plans: {my_plans.count()}")
                for plan in my_plans[:3]:
                    goals_count = TreatmentGoal.objects.filter(treatment_plan=plan).count()
                    context_parts.append(f"- {plan.plan_type} ({goals_count} goals)")
            
        elif role_name in ['Admin', 'Superadmin']:
            # Admin specific info - BUSINESS OVERVIEW
            context_parts.append("=== BUSINESS OVERVIEW ===")
            
            # Get business overview data (filtered by involvement if supervisor)
            business_data = build_business_overview_context(user)
            
            # Add key metrics to context
            if 'summary' in business_data:
                context_parts.append(business_data['summary'])
            
            if 'user_statistics' in business_data:
                stats = business_data['user_statistics']
                context_parts.append(f"Total Users: {stats.get('total_users', 0)}")
                context_parts.append(f"Active Users: {stats.get('active_users', 0)}")
                context_parts.append(f"Total Clients: {stats.get('total_clients', 0)}")
                context_parts.append(f"Total Staff (RBT/BCBA): {stats.get('total_staff', 0)}")
            
            if 'session_statistics' in business_data:
                stats = business_data['session_statistics']
                context_parts.append(f"Total Sessions: {stats.get('total_sessions', 0)}")
                context_parts.append(f"Completed Sessions: {stats.get('completed_sessions', 0)}")
                context_parts.append(f"Upcoming Sessions: {stats.get('upcoming_sessions', 0)}")
                context_parts.append(f"Attendance Rate: {stats.get('attendance_rate', 0)}%")
            
            if 'goal_statistics' in business_data:
                stats = business_data['goal_statistics']
                context_parts.append(f"Total Goals Tracked: {stats.get('total_goals', 0)}")
                context_parts.append(f"Goals Achieved: {stats.get('met_goals', 0)}")
                context_parts.append(f"Goal Achievement Rate: {stats.get('achievement_rate', 0)}%")
            
            if 'treatment_plan_statistics' in business_data:
                stats = business_data['treatment_plan_statistics']
                context_parts.append(f"Total Treatment Plans: {stats.get('total_plans', 0)}")
                context_parts.append(f"Approved Plans: {stats.get('approved_plans', 0)}")
            
            # Get subordinates if user is a supervisor
            subordinates = CustomUser.objects.filter(supervisor=user)
            if subordinates:
                context_parts.append(f"Subordinates: {subordinates.count()}")
                for subordinate in subordinates[:5]:
                    context_parts.append(f"- {subordinate.name or subordinate.username} ({subordinate.role.name if subordinate.role else 'No role'})")
    
    # Goals and session focus
    if user.goals:
        context_parts.append(f"Personal Goals: {user.goals}")
    if user.session_focus:
        context_parts.append(f"Session Focus: {user.session_focus}")
    
    return "\n".join(context_parts)


def build_business_overview_context(user):
    """
    Build comprehensive business overview context for admin users.
    All data is filtered based on user involvement (supervisor relationships).
    """
    from api.models import CustomUser
    from session.models import Session, GoalProgress, Incident
    from treatment_plan.models import TreatmentPlan, TreatmentGoal
    from django.db.models import Count, Q, Avg
    from datetime import timedelta
    
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    # Determine if user has supervisory scope (filter by subordinates)
    has_supervisor_scope = CustomUser.objects.filter(supervisor=user).exists()
    
    # Base querysets - filter by involvement
    if has_supervisor_scope and user.role.name != 'Superadmin':
        # If user is supervisor, only show data for subordinates and their related data
        subordinates = CustomUser.objects.filter(supervisor=user)
        subordinate_ids = list(subordinates.values_list('id', flat=True))
        
        # Users in scope: subordinates + self
        users_in_scope = CustomUser.objects.filter(
            Q(id__in=subordinate_ids) | Q(id=user.id)
        )
        clients_in_scope = users_in_scope.filter(role__name='Clients/Parent')
        staff_in_scope = users_in_scope.filter(role__name__in=['RBT', 'BCBA'])
    else:
        # Superadmin or admin without supervisor scope - see all data
        users_in_scope = CustomUser.objects.all()
        clients_in_scope = CustomUser.objects.filter(role__name='Clients/Parent')
        staff_in_scope = CustomUser.objects.filter(role__name__in=['RBT', 'BCBA'])
    
    # User Statistics
    total_users = users_in_scope.count()
    active_users = users_in_scope.filter(status='Active').count()
    total_clients = clients_in_scope.count()
    total_staff = staff_in_scope.count()
    
    # Session Statistics - only sessions involving users in scope
    sessions_qs = Session.objects.filter(
        Q(client__in=clients_in_scope) | Q(staff__in=staff_in_scope)
    ) if has_supervisor_scope and user.role.name != 'Superadmin' else Session.objects.all()
    
    total_sessions = sessions_qs.count()
    completed_sessions = sessions_qs.filter(status='completed').count()
    upcoming_sessions = sessions_qs.filter(
        session_date__gte=today,
        status__in=['scheduled', 'in_progress']
    ).count()
    cancelled_sessions = sessions_qs.filter(status='cancelled').count()
    
    # Calculate attendance rate
    total_scheduled = completed_sessions + cancelled_sessions
    attendance_rate = (completed_sessions / total_scheduled * 100) if total_scheduled > 0 else 0
    
    # Recent sessions (last 30 days)
    recent_sessions = sessions_qs.filter(
        session_date__gte=last_30_days
    ).count()
    
    # Goal Statistics - only goals for sessions in scope
    completed_session_ids = sessions_qs.filter(status='completed').values_list('id', flat=True)
    goals_qs = GoalProgress.objects.filter(session_id__in=completed_session_ids)
    
    total_goals = goals_qs.count()
    met_goals = goals_qs.filter(is_met=True).count()
    achievement_rate = (met_goals / total_goals * 100) if total_goals > 0 else 0
    
    # Treatment Plan Statistics - only plans for clients in scope
    if has_supervisor_scope and user.role.name != 'Superadmin':
        plans_qs = TreatmentPlan.objects.filter(
            Q(bcba__in=staff_in_scope) | Q(client_id__in=[str(c.id) for c in clients_in_scope])
        )
    else:
        plans_qs = TreatmentPlan.objects.all()
    
    total_plans = plans_qs.count()
    approved_plans = plans_qs.filter(status='approved').count()
    draft_plans = plans_qs.filter(status='draft').count()
    
    # Treatment Goals
    plans_ids = plans_qs.values_list('id', flat=True)
    treatment_goals_qs = TreatmentGoal.objects.filter(treatment_plan_id__in=plans_ids)
    total_treatment_goals = treatment_goals_qs.count()
    achieved_treatment_goals = treatment_goals_qs.filter(is_achieved=True).count()
    
    # Incident Statistics
    incidents_qs = Incident.objects.filter(session__in=sessions_qs)
    total_incidents = incidents_qs.count()
    recent_incidents = incidents_qs.filter(
        session__session_date__gte=last_30_days
    ).count()
    
    # Staff Productivity (last 7 days)
    staff_productivity = {}
    for staff in staff_in_scope[:10]:  # Top 10 staff
        staff_sessions = sessions_qs.filter(
            staff=staff,
            session_date__gte=last_7_days,
            status='completed'
        ).count()
        if staff_sessions > 0:
            staff_productivity[staff.name or staff.username] = staff_sessions
    
    # Client Progress (top clients)
    client_progress = []
    for client in clients_in_scope[:10]:  # Top 10 clients
        client_sessions = sessions_qs.filter(client=client, status='completed').count()
        client_goals = GoalProgress.objects.filter(
            session__client=client,
            session__status='completed'
        )
        client_met_goals = client_goals.filter(is_met=True).count()
        client_total_goals = client_goals.count()
        client_achievement = (client_met_goals / client_total_goals * 100) if client_total_goals > 0 else 0
        
        if client_sessions > 0:
            client_progress.append({
                'name': client.name or client.username,
                'sessions': client_sessions,
                'goal_achievement': round(client_achievement, 2)
            })
    
    # Build summary
    summary = f"""Business Overview Summary:
- Total Users: {total_users} (Active: {active_users})
- Total Clients: {total_clients}
- Total Staff: {total_staff}
- Total Sessions: {total_sessions} (Completed: {completed_sessions}, Upcoming: {upcoming_sessions})
- Attendance Rate: {round(attendance_rate, 2)}%
- Goal Achievement Rate: {round(achievement_rate, 2)}%
- Treatment Plans: {total_plans} (Approved: {approved_plans})
- Total Incidents: {total_incidents} (Recent: {recent_incidents})"""
    
    return {
        'summary': summary,
        'user_statistics': {
            'total_users': total_users,
            'active_users': active_users,
            'total_clients': total_clients,
            'total_staff': total_staff,
            'scope': 'supervisor_scope' if has_supervisor_scope and user.role.name != 'Superadmin' else 'all_data'
        },
        'session_statistics': {
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'upcoming_sessions': upcoming_sessions,
            'cancelled_sessions': cancelled_sessions,
            'attendance_rate': round(attendance_rate, 2),
            'recent_sessions_30_days': recent_sessions
        },
        'goal_statistics': {
            'total_goals': total_goals,
            'met_goals': met_goals,
            'achievement_rate': round(achievement_rate, 2)
        },
        'treatment_plan_statistics': {
            'total_plans': total_plans,
            'approved_plans': approved_plans,
            'draft_plans': draft_plans,
            'total_treatment_goals': total_treatment_goals,
            'achieved_treatment_goals': achieved_treatment_goals
        },
        'incident_statistics': {
            'total_incidents': total_incidents,
            'recent_incidents_30_days': recent_incidents
        },
        'staff_productivity': staff_productivity,
        'client_progress': client_progress,
        'calculated_at': timezone.now().isoformat()
    }


def generate_session_notes(session_data: dict) -> str:
    """
    Generate comprehensive professional session notes using GPT-4 based on all session data.
    
    Args:
        session_data: Dictionary containing all session information including:
            - session_info (client, staff, date, time, location, etc.)
            - activities (list of activities performed)
            - goals (goal progress and trial data)
            - abc_events (behavioral observations)
            - reinforcement_strategies (reinforcement used)
            - incidents (any incidents)
            - checklist (pre-session items)
            
    Returns:
        str: Professional, comprehensive session notes in markdown format
    """
    openai.api_key = settings.OPENAI_API_KEY

    if not openai.api_key:
        return "AI error: OpenAI API key not configured"

    try:
        # Create a structured prompt for the AI
        prompt = f"""You are an experienced Board Certified Behavior Analyst (BCBA) writing professional ABA therapy session notes. 

Generate comprehensive, professional session notes based on the following session data:

SESSION INFORMATION:
{session_data.get('session_info', {})}

ACTIVITIES PERFORMED:
{session_data.get('activities', [])}

GOAL PROGRESS:
{session_data.get('goals', [])}

ABC (BEHAVIORAL) EVENTS:
{session_data.get('abc_events', [])}

REINFORCEMENT STRATEGIES:
{session_data.get('reinforcement_strategies', [])}

INCIDENTS:
{session_data.get('incidents', [])}

PRE-SESSION CHECKLIST:
{session_data.get('checklist', {})}

Please generate professional session notes that include:
1. Session Overview (brief summary)
2. Client Engagement and Behavior Summary
3. Detailed Goal Progress with data (trials, successes, percentages)
4. Behavioral Observations (ABC analysis if applicable)
5. Reinforcement Effectiveness
6. Incidents and Interventions (if any)
7. Recommendations for next session

Use professional ABA terminology. Be specific with data and observations. Format the notes in clear sections using markdown."""

        messages = [
            {
                "role": "system", 
                "content": "You are an expert BCBA writing professional, detailed ABA therapy session notes. Your notes are clear, data-driven, and follow best practices in Applied Behavior Analysis documentation."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1000,  # Allow for comprehensive notes
            temperature=0.3  # Slightly creative but mostly factual
        )

        ai_notes = response.choices[0].message.content
        return ai_notes

    except Exception as e:
        return f"AI error generating session notes: {str(e)}"


def generate_bcba_session_analysis(session_data: dict, rbt_name: str = "", client_name: str = "") -> str:
    """
    Generate comprehensive BCBA analysis notes for an RBT session.
    This is from a supervisor/review perspective, analyzing the session quality,
    implementation fidelity, and providing feedback.
    
    Args:
        session_data: Dictionary containing all session information including:
            - session_info (client, staff, date, time, location, etc.)
            - activities (list of activities performed)
            - goals (goal progress and trial data)
            - abc_events (behavioral observations)
            - reinforcement_strategies (reinforcement used)
            - incidents (any incidents)
            - checklist (pre-session items)
        rbt_name: Name of the RBT who conducted the session
        client_name: Name of the client
        
    Returns:
        str: Comprehensive BCBA analysis and review notes in markdown format
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', None))

        if not client.api_key:
            return "AI error: OpenAI API key not configured"
        # Create a structured prompt for BCBA analysis
        prompt = f"""You are a Board Certified Behavior Analyst (BCBA) reviewing and analyzing an ABA therapy session conducted by an RBT (Registered Behavior Technician).

Your role is to provide a comprehensive supervisory analysis of this session, including:
1. Session quality and implementation fidelity
2. Data collection accuracy
3. Goal progress analysis
4. Behavioral intervention effectiveness
5. Areas of strength and improvement
6. Recommendations for the RBT
7. Recommendations for future sessions

SESSION INFORMATION:
RBT: {rbt_name}
Client: {client_name}
{session_data.get('session_info', {})}

ACTIVITIES PERFORMED:
{session_data.get('activities', [])}

GOAL PROGRESS:
{session_data.get('goals', [])}

ABC (BEHAVIORAL) EVENTS:
{session_data.get('abc_events', [])}

REINFORCEMENT STRATEGIES:
{session_data.get('reinforcement_strategies', [])}

INCIDENTS:
{session_data.get('incidents', [])}

PRE-SESSION CHECKLIST:
{session_data.get('checklist', {})}

Please generate a comprehensive BCBA analysis that includes:

1. **Session Overview & Summary**
   - Overall session quality assessment
   - Client engagement level
   - Session structure and flow

2. **Implementation Fidelity Review**
   - Adherence to treatment plan protocols
   - Data collection accuracy and completeness
   - Proper use of reinforcement strategies
   - Prompting hierarchy implementation

3. **Goal Progress Analysis**
   - Detailed analysis of goal achievement data
   - Trend identification (improving, maintaining, declining)
   - Trial-by-trial analysis if applicable
   - Recommendations for goal modifications if needed

4. **Behavioral Observations & ABC Analysis**
   - Quality of ABC data collection
   - Behavioral patterns identified
   - Antecedent and consequence analysis
   - Effectiveness of interventions

5. **Strengths & Areas for Improvement**
   - What the RBT did well
   - Areas needing additional training or support
   - Specific actionable feedback

6. **Clinical Recommendations**
   - Recommendations for next session
   - Treatment plan modifications if needed
   - Training or supervision needs for RBT
   - Parent/caregiver communication points

Use professional BCBA supervisory language. Be specific, data-driven, and constructive. Format the analysis in clear sections using markdown. Provide actionable feedback that helps improve service quality."""

        messages = [
            {
                "role": "system", 
                "content": "You are an expert BCBA providing supervisory analysis and review of ABA therapy sessions. Your analysis is thorough, professional, data-driven, and focuses on implementation fidelity, service quality, and clinical recommendations. You provide constructive feedback to help RBTs improve their practice."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]

        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=2000,  # More tokens for comprehensive analysis
            temperature=0.3  # Slightly creative but mostly factual
        )

        bcba_analysis = response.choices[0].message.content
        return bcba_analysis

    except Exception as e:
        return f"AI error generating BCBA analysis: {str(e)}"