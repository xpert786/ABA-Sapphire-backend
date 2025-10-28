# Ocean AI Suggestions & Questions During Sessions

## 🤖 **Complete Ocean AI Active Prompting System**

### **1. Automatic Session Monitoring & Suggestions**

#### **A. Time-Based Suggestions**
```python
# Ocean AI automatically suggests based on session timing
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_ocean_suggestions(request, session_id):
    """
    Get Ocean AI suggestions based on session progress and timing
    """
    session = get_object_or_404(Session, id=session_id)
    
    # Calculate session progress
    now = timezone.now().time()
    session_start = session.start_time
    session_end = session.end_time
    total_duration = (session_end.hour * 60 + session_end.minute) - (session_start.hour * 60 + session_start.minute)
    elapsed_time = (now.hour * 60 + now.minute) - (session_start.hour * 60 + session_start.minute)
    progress_percentage = (elapsed_time / total_duration) * 100 if total_duration > 0 else 0
    
    suggestions = []
    
    # Time-based suggestions
    if progress_percentage < 25:
        suggestions.append({
            "type": "session_start",
            "message": "🌊 Ocean: Great start! How is the client settling in? Any initial observations to note?",
            "priority": "high",
            "action": "engagement_check"
        })
    elif progress_percentage < 50:
        suggestions.append({
            "type": "mid_session",
            "message": "🌊 Ocean: We're halfway through! How are the goals progressing? Any behaviors to document?",
            "priority": "medium",
            "action": "goal_check"
        })
    elif progress_percentage < 75:
        suggestions.append({
            "type": "session_wind_down",
            "message": "🌊 Ocean: Session winding down soon. How effective were your reinforcement strategies today?",
            "priority": "medium",
            "action": "reinforcement_check"
        })
    else:
        suggestions.append({
            "type": "session_ending",
            "message": "🌊 Ocean: Session ending soon! Ready to wrap up and generate your session note?",
            "priority": "high",
            "action": "session_wrap"
        })
    
    return Response({
        "session_id": session_id,
        "progress_percentage": progress_percentage,
        "suggestions": suggestions,
        "time_remaining": total_duration - elapsed_time
    })
```

#### **B. Data-Driven Suggestions**
```python
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_data_driven_suggestions(request, session_id):
    """
    Get Ocean AI suggestions based on session data patterns
    """
    session = get_object_or_404(Session, id=session_id)
    
    suggestions = []
    
    # Check activities
    activities_count = session.activities.count()
    if activities_count == 0:
        suggestions.append({
            "type": "missing_data",
            "message": "🌊 Ocean: No activities logged yet. What activities are you working on with the client?",
            "priority": "high",
            "action": "log_activity"
        })
    elif activities_count < 2:
        suggestions.append({
            "type": "data_encouragement",
            "message": "🌊 Ocean: Good start with activities! Consider adding more variety to keep the client engaged.",
            "priority": "medium",
            "action": "add_activity"
        })
    
    # Check goals
    goals_count = session.goal_progress.count()
    if goals_count == 0:
        suggestions.append({
            "type": "missing_data",
            "message": "🌊 Ocean: No goal progress tracked yet. How is the client performing on their targets?",
            "priority": "high",
            "action": "track_goals"
        })
    
    # Check ABC events
    abc_count = session.abc_events.count()
    if abc_count == 0:
        suggestions.append({
            "type": "behavioral_observation",
            "message": "🌊 Ocean: No behavioral observations logged. Any notable behaviors or incidents to document?",
            "priority": "medium",
            "action": "log_behavior"
        })
    
    # Check reinforcement strategies
    reinforcement_count = session.reinforcement_strategies.count()
    if reinforcement_count == 0:
        suggestions.append({
            "type": "missing_data",
            "message": "🌊 Ocean: No reinforcement strategies logged. What's working to motivate the client today?",
            "priority": "medium",
            "action": "log_reinforcement"
        })
    
    return Response({
        "session_id": session_id,
        "suggestions": suggestions,
        "data_summary": {
            "activities": activities_count,
            "goals": goals_count,
            "abc_events": abc_count,
            "reinforcement_strategies": reinforcement_count
        }
    })
```

### **2. Smart Question Generation**

#### **A. Context-Aware Questions**
```python
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_smart_questions(request, session_id):
    """
    Generate smart questions based on session context and client data
    """
    session = get_object_or_404(Session, id=session_id)
    
    # Get client context
    client = session.client
    client_context = {
        "name": client.name,
        "goals": getattr(client, 'goals', ''),
        "session_focus": getattr(client, 'session_focus', ''),
        "previous_sessions": Session.objects.filter(client=client).count()
    }
    
    # Generate contextual questions
    questions = []
    
    # Client-specific questions
    if client_context["goals"]:
        questions.append({
            "type": "goal_focused",
            "message": f"🌊 Ocean: I see {client.name}'s focus is on '{client_context['goals']}'. How is progress on this goal today?",
            "priority": "high"
        })
    
    # Session-specific questions
    if session.service_type == "ABA":
        questions.append({
            "type": "aba_specific",
            "message": "🌊 Ocean: Any challenging behaviors to address today? How is the client responding to interventions?",
            "priority": "medium"
        })
    
    # Time-based questions
    now = timezone.now().time()
    if now.hour >= 14:  # Afternoon sessions
        questions.append({
            "type": "afternoon_session",
            "message": "🌊 Ocean: Afternoon sessions can be challenging. How is the client's energy level? Any fatigue concerns?",
            "priority": "medium"
        })
    
    return Response({
        "session_id": session_id,
        "client_context": client_context,
        "questions": questions
    })
```

#### **B. Adaptive Question System**
```python
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_adaptive_questions(request, session_id):
    """
    Get adaptive questions based on session progress and RBT responses
    """
    session = get_object_or_404(Session, id=session_id)
    
    # Get recent prompts and responses
    recent_prompts = SessionPrompt.objects.filter(
        session=session,
        created_at__gte=timezone.now() - timedelta(minutes=30)
    ).order_by('-created_at')
    
    questions = []
    
    # If no recent engagement
    if not recent_prompts.filter(prompt_type='engagement').exists():
        questions.append({
            "type": "engagement",
            "message": "🌊 Ocean: How is the session going? Are you and the client both engaged?",
            "priority": "high",
            "follow_up": "What's working well today?"
        })
    
    # If no goal progress tracked
    if not recent_prompts.filter(prompt_type='goal_check').exists():
        questions.append({
            "type": "goal_progress",
            "message": "🌊 Ocean: How are the client's goals progressing? Any notable achievements or challenges?",
            "priority": "high",
            "follow_up": "What specific targets are you working on?"
        })
    
    # If no behavioral observations
    if not recent_prompts.filter(prompt_type='behavior_tracking').exists():
        questions.append({
            "type": "behavior_observation",
            "message": "🌊 Ocean: Any significant behaviors to note? How is the client responding to your interventions?",
            "priority": "medium",
            "follow_up": "Any ABC patterns you're noticing?"
        })
    
    return Response({
        "session_id": session_id,
        "questions": questions,
        "recent_activity": len(recent_prompts)
    })
```

### **3. Real-Time Session Coaching**

#### **A. Live Session Coaching**
```python
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def get_live_coaching(request, session_id):
    """
    Provide live coaching suggestions during the session
    """
    session = get_object_or_404(Session, id=session_id)
    coaching_data = request.data
    
    coaching_suggestions = []
    
    # Analyze session data for coaching opportunities
    if coaching_data.get('client_engagement') == 'low':
        coaching_suggestions.append({
            "type": "engagement_coaching",
            "message": "🌊 Ocean: Client seems less engaged. Try switching activities or using preferred reinforcers.",
            "suggestions": [
                "Take a short break",
                "Use more preferred activities",
                "Increase reinforcement frequency",
                "Check for environmental distractions"
            ]
        })
    
    if coaching_data.get('goal_progress') == 'slow':
        coaching_suggestions.append({
            "type": "goal_coaching",
            "message": "🌊 Ocean: Goal progress seems slow. Consider adjusting your approach.",
            "suggestions": [
                "Break down the goal into smaller steps",
                "Use more prompting if needed",
                "Increase reinforcement for attempts",
                "Check if the goal is appropriate for today"
            ]
        })
    
    if coaching_data.get('behavior_challenges'):
        coaching_suggestions.append({
            "type": "behavior_coaching",
            "message": "🌊 Ocean: I notice some behavioral challenges. Here are some strategies:",
            "suggestions": [
                "Use antecedent strategies to prevent issues",
                "Implement consistent consequences",
                "Document ABC patterns for analysis",
                "Consider environmental modifications"
            ]
        })
    
    return Response({
        "session_id": session_id,
        "coaching_suggestions": coaching_suggestions,
        "timestamp": timezone.now()
    })
```

### **4. Proactive Session Management**

#### **A. Session Health Check**
```python
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def session_health_check(request, session_id):
    """
    Comprehensive session health check with Ocean AI recommendations
    """
    session = get_object_or_404(Session, id=session_id)
    
    # Calculate session metrics
    activities_count = session.activities.count()
    goals_count = session.goal_progress.count()
    abc_count = session.abc_events.count()
    reinforcement_count = session.reinforcement_strategies.count()
    
    # Session health score
    health_score = 0
    if activities_count > 0: health_score += 25
    if goals_count > 0: health_score += 25
    if abc_count > 0: health_score += 25
    if reinforcement_count > 0: health_score += 25
    
    # Generate recommendations
    recommendations = []
    
    if health_score < 50:
        recommendations.append({
            "type": "data_collection",
            "message": "🌊 Ocean: Session data collection is incomplete. Focus on documenting key activities and observations.",
            "priority": "high"
        })
    
    if activities_count == 0:
        recommendations.append({
            "type": "activity_logging",
            "message": "🌊 Ocean: No activities logged yet. What are you working on with the client?",
            "priority": "high"
        })
    
    if goals_count == 0:
        recommendations.append({
            "type": "goal_tracking",
            "message": "🌊 Ocean: No goal progress tracked. How is the client performing on their targets?",
            "priority": "high"
        })
    
    return Response({
        "session_id": session_id,
        "health_score": health_score,
        "metrics": {
            "activities": activities_count,
            "goals": goals_count,
            "abc_events": abc_count,
            "reinforcement_strategies": reinforcement_count
        },
        "recommendations": recommendations,
        "session_status": "healthy" if health_score >= 75 else "needs_attention"
    })
```

### **5. Complete cURL Commands for Testing**

#### **A. Get Ocean Suggestions**
```bash
curl -X GET "http://168.231.121.7/sapphire/session/sessions/5/ocean-suggestions/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### **B. Get Data-Driven Suggestions**
```bash
curl -X GET "http://168.231.121.7/sapphire/session/sessions/5/data-driven-suggestions/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### **C. Generate Smart Questions**
```bash
curl -X POST "http://168.231.121.7/sapphire/session/sessions/5/smart-questions/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

#### **D. Get Live Coaching**
```bash
curl -X POST "http://168.231.121.7/sapphire/session/sessions/5/live-coaching/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_engagement": "low",
    "goal_progress": "slow",
    "behavior_challenges": true
  }'
```

#### **E. Session Health Check**
```bash
curl -X GET "http://168.231.121.7/sapphire/session/sessions/5/session-health-check/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **6. Frontend Integration**

#### **A. Real-Time Suggestions Display**
```javascript
// Ocean AI Suggestions Component
const OceanSuggestions = ({ sessionId }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchSuggestions = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`/api/sessions/${sessionId}/ocean-suggestions/`);
        const data = await response.json();
        setSuggestions(data.suggestions);
      } catch (error) {
        console.error('Error fetching suggestions:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSuggestions();
    const interval = setInterval(fetchSuggestions, 60000); // Check every minute
    return () => clearInterval(interval);
  }, [sessionId]);

  return (
    <div className="ocean-suggestions">
      <h3>🌊 Ocean AI Suggestions</h3>
      {isLoading ? (
        <p>Loading suggestions...</p>
      ) : (
        suggestions.map((suggestion, index) => (
          <div key={index} className={`suggestion ${suggestion.priority}`}>
            <p>{suggestion.message}</p>
            {suggestion.suggestions && (
              <ul>
                {suggestion.suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            )}
          </div>
        ))
      )}
    </div>
  );
};
```

#### **B. Smart Question Interface**
```javascript
// Smart Questions Component
const SmartQuestions = ({ sessionId }) => {
  const [questions, setQuestions] = useState([]);

  const generateQuestions = async () => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}/smart-questions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      setQuestions(data.questions);
    } catch (error) {
      console.error('Error generating questions:', error);
    }
  };

  return (
    <div className="smart-questions">
      <button onClick={generateQuestions}>Generate Smart Questions</button>
      {questions.map((question, index) => (
        <div key={index} className="question">
          <p>{question.message}</p>
          {question.follow_up && <p><em>{question.follow_up}</em></p>}
        </div>
      ))}
    </div>
  );
};
```

### **7. Expected Responses**

#### **A. Ocean Suggestions Response**
```json
{
  "session_id": 5,
  "progress_percentage": 45,
  "suggestions": [
    {
      "type": "mid_session",
      "message": "🌊 Ocean: We're halfway through! How are the goals progressing? Any behaviors to document?",
      "priority": "medium",
      "action": "goal_check"
    }
  ],
  "time_remaining": 30
}
```

#### **B. Smart Questions Response**
```json
{
  "session_id": 5,
  "client_context": {
    "name": "Sophia M.",
    "goals": "Requesting help and following instructions",
    "session_focus": "Communication skills",
    "previous_sessions": 12
  },
  "questions": [
    {
      "type": "goal_focused",
      "message": "🌊 Ocean: I see Sophia's focus is on 'Requesting help and following instructions'. How is progress on this goal today?",
      "priority": "high"
    }
  ]
}
```

This system provides comprehensive Ocean AI suggestions and questions throughout the session, keeping RBTs engaged and ensuring quality session documentation!

