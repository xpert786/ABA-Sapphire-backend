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
    """
    openai.api_key = settings.OPENAI_API_KEY

    if not openai.api_key:
        return "AI error: API key not set"

    try:
        # Gather user-specific context from database
        context = build_user_context(user)
        
        system_prompt = f"""You are an AI assistant for a healthcare/ABA therapy management system. 
        You have access to the following user context:
        
        {context}
        
        Provide helpful, accurate responses based on this context. If the user asks about their data, 
        use the information provided. Be professional and supportive."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=300,  # Increased for more detailed responses
            temperature=0.3  # Slightly more creative but still factual
        )

        ai_text = response.choices[0].message.content
        return ai_text

    except Exception as e:
        return f"AI error: {e}"


def build_user_context(user):
    """
    Build context string from user's database information.
    """
    from api.models import CustomUser
    from scheduler.models import Session
    from session.models import Session as TherapySession
    
    context_parts = []
    
    # Basic user info
    context_parts.append(f"User: {user.name} ({user.username})")
    context_parts.append(f"Role: {user.role.name if user.role else 'No role assigned'}")
    context_parts.append(f"Email: {user.email}")
    context_parts.append(f"Status: {user.status}")
    
    # Supervisor info
    if user.supervisor:
        context_parts.append(f"Supervisor: {user.supervisor.name} ({user.supervisor.role.name if user.supervisor.role else 'No role'})")
    
    # Role-specific context
    if user.role:
        if user.role.name == 'RBT':
            # RBT specific info
            context_parts.append(f"Staff ID: {user.staff_id}")
            if user.assigned_bcba:
                context_parts.append(f"Assigned BCBA: {user.assigned_bcba.name}")
            
            # Get upcoming sessions
            upcoming_sessions = Session.objects.filter(
                staff=user,
                session_date__gte=timezone.now().date()
            ).order_by('session_date', 'start_time')[:5]
            
            if upcoming_sessions:
                context_parts.append("Upcoming sessions:")
                for session in upcoming_sessions:
                    context_parts.append(f"- {session.session_date} at {session.start_time} with {session.client.name}")
            
        elif user.role.name == 'BCBA':
            # BCBA specific info
            context_parts.append(f"Staff ID: {user.staff_id}")
            
            # Get supervised RBTs
            supervised_rbts = CustomUser.objects.filter(assigned_bcba=user)
            if supervised_rbts:
                context_parts.append("Supervised RBTs:")
                for rbt in supervised_rbts:
                    context_parts.append(f"- {rbt.name} ({rbt.staff_id})")
            
        elif user.role.name == 'Clients/Parent':
            # Client specific info
            context_parts.append(f"Client ID: {user.staff_id}")
            if user.assigned_rbt:
                context_parts.append(f"Assigned RBT: {user.assigned_rbt.name}")
            if user.assigned_bcba:
                context_parts.append(f"Assigned BCBA: {user.assigned_bcba.name}")
            
            # Get upcoming sessions
            upcoming_sessions = Session.objects.filter(
                client=user,
                session_date__gte=timezone.now().date()
            ).order_by('session_date', 'start_time')[:5]
            
            if upcoming_sessions:
                context_parts.append("Upcoming sessions:")
                for session in upcoming_sessions:
                    context_parts.append(f"- {session.session_date} at {session.start_time} with {session.staff.name if session.staff else 'TBD'}")
            
        elif user.role.name in ['Admin', 'Superadmin']:
            # Admin specific info
            context_parts.append("Administrative access")
            
            # Get subordinates
            subordinates = CustomUser.objects.filter(supervisor=user)
            if subordinates:
                context_parts.append("Subordinates:")
                for subordinate in subordinates:
                    context_parts.append(f"- {subordinate.name} ({subordinate.role.name if subordinate.role else 'No role'})")
    
    # Goals and session focus
    if user.goals:
        context_parts.append(f"Goals: {user.goals}")
    if user.session_focus:
        context_parts.append(f"Session Focus: {user.session_focus}")
    
    return "\n".join(context_parts)


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