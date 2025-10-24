# Session API Testing Guide

This guide provides comprehensive examples for testing the Session API using both Postman and curl commands.

## Base URL
```
http://localhost:8000/sapphire/session/
```

## Authentication
All API endpoints require JWT authentication. Include the access token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

## 1. Authentication (Get JWT Token)

### Login to get JWT token
```bash
curl -X POST http://localhost:8000/sapphire/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

**Postman:**
- Method: POST
- URL: `http://localhost:8000/sapphire/api/auth/login/`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

## 2. Session Endpoints

### 2.1 Get All Sessions (Role-Based Access)

```bash
curl -X GET http://localhost:8000/sapphire/session/sessions/ \
  -H "Authorization: Bearer <your_access_token>"
```

**With Query Parameters:**
```bash
# Filter by status
curl -X GET "http://localhost:8000/sapphire/session/sessions/?status=completed" \
  -H "Authorization: Bearer <your_access_token>"

# Filter by date range
curl -X GET "http://localhost:8000/sapphire/session/sessions/?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer <your_access_token>"

# Filter by client (admin only)
curl -X GET "http://localhost:8000/sapphire/session/sessions/?client_id=4" \
  -H "Authorization: Bearer <admin_access_token>"

# Filter by staff (admin only)
curl -X GET "http://localhost:8000/sapphire/session/sessions/?staff_id=6" \
  -H "Authorization: Bearer <admin_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/session/sessions/`
- Headers: `Authorization: Bearer <your_access_token>`
- Query Params (optional):
  - `status`: scheduled, in_progress, completed, cancelled
  - `start_date`: YYYY-MM-DD format
  - `end_date`: YYYY-MM-DD format
  - `client_id`: Client ID (admin only)
  - `staff_id`: Staff ID (admin only)

### 2.2 Get Specific Session

```bash
curl -X GET http://localhost:8000/sapphire/session/sessions/2/ \
  -H "Authorization: Bearer <your_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/session/sessions/2/`
- Headers: `Authorization: Bearer <your_access_token>`

### 2.3 Create New Session

```bash
curl -X POST http://localhost:8000/sapphire/session/sessions/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "client": 4,
    "session_date": "2024-01-15",
    "start_time": "09:00:00",
    "end_time": "10:00:00",
    "location": "Clinic Room A",
    "service_type": "ABA",
    "session_notes": "Initial assessment session"
  }'
```

**Postman:**
- Method: POST
- URL: `http://localhost:8000/sapphire/session/sessions/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <your_access_token>`
- Body (raw JSON): [Session data as above]

### 2.4 Update Session

```bash
curl -X PUT http://localhost:8000/sapphire/session/sessions/2/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "client": 4,
    "session_date": "2024-01-15",
    "start_time": "09:00:00",
    "end_time": "10:00:00",
    "location": "Clinic Room B",
    "service_type": "ABA",
    "status": "in_progress",
    "session_notes": "Updated session notes"
  }'
```

**Postman:**
- Method: PUT
- URL: `http://localhost:8000/sapphire/session/sessions/2/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <your_access_token>`
- Body (raw JSON): [Updated session data]

### 2.5 Get Upcoming Sessions

```bash
curl -X GET http://localhost:8000/sapphire/session/upcoming-sessions/ \
  -H "Authorization: Bearer <your_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/session/upcoming-sessions/`
- Headers: `Authorization: Bearer <your_access_token>`

### 2.6 Get Session Statistics

```bash
curl -X GET http://localhost:8000/sapphire/session/sessions/statistics/ \
  -H "Authorization: Bearer <your_access_token>"
```

**With Date Range:**
```bash
curl -X GET "http://localhost:8000/sapphire/session/sessions/statistics/?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer <your_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/session/sessions/statistics/`
- Headers: `Authorization: Bearer <your_access_token>`
- Query Params (optional):
  - `start_date`: YYYY-MM-DD format
  - `end_date`: YYYY-MM-DD format

### 2.7 Get User Sessions (Admin Only)

```bash
curl -X GET "http://localhost:8000/sapphire/session/sessions/user-sessions/?user_id=6" \
  -H "Authorization: Bearer <admin_access_token>"
```

**With Filters:**
```bash
curl -X GET "http://localhost:8000/sapphire/session/sessions/user-sessions/?user_id=6&status=completed&start_date=2024-01-01" \
  -H "Authorization: Bearer <admin_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/session/sessions/user-sessions/`
- Headers: `Authorization: Bearer <admin_access_token>`
- Query Params:
  - `user_id`: Required - User ID to get sessions for
  - `status`: Optional - Filter by status
  - `start_date`: Optional - Filter by start date
  - `end_date`: Optional - Filter by end date

### 2.8 Get User Details by ID

```bash
curl -X GET http://localhost:8000/sapphire/session/users/6/details/ \
  -H "Authorization: Bearer <your_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/session/users/6/details/`
- Headers: `Authorization: Bearer <your_access_token>`

**Note:** 
- **Admin/Superadmin**: Can view any user's details
- **Regular users**: Can only view their own details

### 2.9 Get BCBA Client List

```bash
curl -X GET http://localhost:8000/sapphire/session/bcba/clients/ \
  -H "Authorization: Bearer <bcba_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/session/bcba/clients/`
- Headers: `Authorization: Bearer <bcba_access_token>`

**Note:** 
- **BCBA**: Can see clients assigned to them via supervisor field, with fallback to session history
- **Admin/Superadmin**: Can see all clients
- **Other roles**: Cannot access this endpoint

### 2.10 Get Treatment Plan Data for RBT Session Form

```bash
curl -X GET http://localhost:8000/sapphire/session/treatment-plan/4/session-data/ \
  -H "Authorization: Bearer <rbt_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/session/treatment-plan/4/session-data/`
- Headers: `Authorization: Bearer <rbt_access_token>`

**Note:** 
- **RBT/BCBA**: Can access treatment plans for their assigned clients
- **Admin/Superadmin**: Can access any client's treatment plan
- **Other roles**: Cannot access this endpoint
- **Status**: Gets the most recent treatment plan regardless of status (draft, pending, approved, etc.)

## 3. Session Timer Endpoints

### 3.1 Get Session Timer

```bash
curl -X GET http://localhost:8000/sapphire/session/sessions/2/timer/ \
  -H "Authorization: Bearer <your_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/session/sessions/2/timer/`
- Headers: `Authorization: Bearer <your_access_token>`

### 3.2 Start Session Timer

```bash
curl -X POST http://localhost:8000/sapphire/session/sessions/2/timer/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "action": "start"
  }'
```

**Postman:**
- Method: POST
- URL: `http://localhost:8000/sapphire/session/sessions/2/timer/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <your_access_token>`
- Body (raw JSON):
```json
{
  "action": "start"
}
```

### 3.3 Stop Session Timer

```bash
curl -X POST http://localhost:8000/sapphire/session/sessions/2/timer/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "action": "stop"
  }'
```

**Postman:**
- Method: POST
- URL: `http://localhost:8000/sapphire/session/sessions/2/timer/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <your_access_token>`
- Body (raw JSON):
```json
{
  "action": "stop"
}
```

## 4. Session Data Endpoints

### 4.1 Get Session Activities

```bash
curl -X GET http://localhost:8000/sapphire/session/sessions/2/activities/ \
  -H "Authorization: Bearer <your_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/session/sessions/2/activities/`
- Headers: `Authorization: Bearer <your_access_token>`

### 4.2 Create Session Activity

```bash
curl -X POST http://localhost:8000/sapphire/session/sessions/2/activities/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "activity_name": "Matching Task",
    "duration_minutes": 15,
    "description": "Visual matching activity with cards",
    "client_response": "Completed successfully with minimal prompting"
  }'
```

**Postman:**
- Method: POST
- URL: `http://localhost:8000/sapphire/session/sessions/2/activities/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <your_access_token>`
- Body (raw JSON): [Activity data as above]

### 4.3 Get Session Goals

```bash
curl -X GET http://localhost:8000/sapphire/session/sessions/2/goal-progress/ \
  -H "Authorization: Bearer <your_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/session/sessions/2/goal-progress/`
- Headers: `Authorization: Bearer <your_access_token>`

### 4.4 Create Session Goal Progress

```bash
curl -X POST http://localhost:8000/sapphire/session/sessions/2/goal-progress/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "goal_name": "Communication",
    "target_behavior": "Request help using PECS",
    "trials_completed": 10,
    "successful_trials": 8,
    "implementation_method": "PECS",
    "notes": "Great progress with visual prompts"
  }'
```

**Postman:**
- Method: POST
- URL: `http://localhost:8000/sapphire/session/sessions/2/goal-progress/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <your_access_token>`
- Body (raw JSON): [Goal progress data as above]

## 5. Ocean AI Integration Endpoints

### 5.1 Get Session Dashboard with Ocean AI

```bash
curl -X GET http://localhost:8000/sapphire/session/sessions/2/ocean-dashboard/ \
  -H "Authorization: Bearer <your_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/session/sessions/2/ocean-dashboard/`
- Headers: `Authorization: Bearer <your_access_token>`

### 5.2 Create Ocean AI Prompt

```bash
curl -X POST http://localhost:8000/sapphire/session/sessions/2/ocean-prompt/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "prompt_type": "engagement"
  }'
```

**Postman:**
- Method: POST
- URL: `http://localhost:8000/sapphire/session/sessions/2/ocean-prompt/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <your_access_token>`
- Body (raw JSON):
```json
{
  "prompt_type": "engagement"
}
```

### 5.3 Respond to Ocean AI Prompt

```bash
curl -X POST http://localhost:8000/sapphire/session/sessions/2/ocean-prompt/1/respond/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "response": "Session is going well. Client is engaged and making good progress on communication goals."
  }'
```

**Postman:**
- Method: POST
- URL: `http://localhost:8000/sapphire/session/sessions/2/ocean-prompt/1/respond/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <your_access_token>`
- Body (raw JSON):
```json
{
  "response": "Session is going well. Client is engaged and making good progress on communication goals."
}
```

### 5.4 Generate AI Session Notes

```bash
curl -X POST http://localhost:8000/sapphire/session/sessions/2/generate-notes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "auto_save": true
  }'
```

**Postman:**
- Method: POST
- URL: `http://localhost:8000/sapphire/session/sessions/2/generate-notes/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <your_access_token>`
- Body (raw JSON):
```json
{
  "auto_save": true
}
```

### 5.5 Save Session Data and Generate Notes

```bash
curl -X POST http://localhost:8000/sapphire/session/sessions/2/save-and-generate-notes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "activities": [
      {
        "name": "Matching Task",
        "duration": 15,
        "description": "Visual matching activity",
        "response": "Completed successfully"
      }
    ],
    "goals": [
      {
        "goal": "Communication",
        "target": "Request help using PECS",
        "trials": 10,
        "successes": 8,
        "percentage": 80,
        "notes": "Great progress"
      }
    ],
    "abc_events": [
      {
        "antecedent": "Asked to clean up",
        "behavior": "Said no and walked away",
        "consequence": "Redirected to task with visual support"
      }
    ],
    "reinforcement_strategies": [
      {
        "type": "Token Economy",
        "description": "Earned tokens for completed tasks",
        "effectiveness": 5,
        "notes": "Very motivating"
      }
    ],
    "incidents": [
      {
        "type": "minor_disruption",
        "description": "Brief refusal to clean up",
        "duration": 2,
        "severity": "low"
      }
    ],
    "checklist": {
      "materials_ready": true,
      "environment_prepared": true,
      "reviewed_goals": true,
      "notes": "All set up properly"
    }
  }'
```

**Postman:**
- Method: POST
- URL: `http://localhost:8000/sapphire/session/sessions/2/save-and-generate-notes/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <your_access_token>`
- Body (raw JSON): [Comprehensive session data as above]

## 6. Role-Based Access Control

### Admin/Superadmin
- Can see all sessions
- Can filter by client_id and staff_id
- Can access user sessions endpoint
- Can see all statistics

### RBT/BCBA
- Can only see sessions they're assigned to
- Cannot filter by client_id or staff_id
- Cannot access user sessions endpoint
- Can only see their own statistics

### Clients/Parent
- Can only see sessions where they are the client
- Cannot create or modify sessions
- Can only view session details

## 7. Sample Response Formats

### Session List Response
```json
[
  {
    "id": 2,
    "client": {
      "id": 4,
      "name": "John Doe",
      "username": "john.doe"
    },
    "staff": {
      "id": 6,
      "name": "Jane Smith",
      "username": "jane.smith"
    },
    "session_date": "2024-01-15",
    "start_time": "09:00:00",
    "end_time": "10:00:00",
    "location": "Clinic Room A",
    "service_type": "ABA",
    "status": "completed",
    "session_notes": "Great session with good progress on communication goals.",
    "created_at": "2024-01-15T08:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

### Session Statistics Response
```json
{
  "total_sessions": 25,
  "completed_sessions": 20,
  "in_progress_sessions": 2,
  "scheduled_sessions": 3,
  "cancelled_sessions": 0,
  "completion_rate": 80.0,
  "recent_sessions_7_days": 5
}
```

### BCBA Client List Response
```json
{
  "bcba": {
    "id": 6,
    "username": "jane.smith",
    "name": "Jane Smith",
    "role": "BCBA"
  },
  "clients": [
    {
      "id": 4,
      "username": "john.doe",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "phone": "+1-555-0124",
      "is_active": true,
      "date_joined": "2024-01-01T08:00:00Z",
      "last_login": "2024-01-15T09:30:00Z",
      "role": {
        "id": 3,
        "name": "Clients/Parent"
      },
      "assignment_status": "directly_assigned",
      "is_directly_assigned": true,
      "session_statistics": {
        "total_sessions": 15,
        "completed_sessions": 12,
        "recent_sessions_30_days": 4,
        "upcoming_sessions": 2,
        "completion_rate": 80.0
      },
      "last_session_date": "2024-01-14T10:00:00Z",
      "last_session_status": "completed"
    },
    {
      "id": 5,
      "username": "sarah.wilson",
      "first_name": "Sarah",
      "last_name": "Wilson",
      "email": "sarah.wilson@example.com",
      "phone": "+1-555-0125",
      "is_active": true,
      "date_joined": "2024-01-05T08:00:00Z",
      "last_login": "2024-01-15T11:00:00Z",
      "role": {
        "id": 3,
        "name": "Clients/Parent"
      },
      "assignment_status": "session_based",
      "is_directly_assigned": false,
      "session_statistics": {
        "total_sessions": 8,
        "completed_sessions": 6,
        "recent_sessions_30_days": 3,
        "upcoming_sessions": 1,
        "completion_rate": 75.0
      },
      "last_session_date": "2024-01-13T14:00:00Z",
      "last_session_status": "completed"
    }
  ],
  "total_clients": 2
}
```

### Treatment Plan Session Data Response
```json
{
  "client": {
    "id": 4,
    "name": "John Doe",
    "username": "john.doe",
    "email": "john.doe@example.com"
  },
  "treatment_plan": {
    "id": 1,
    "plan_type": "comprehensive_aba",
    "client_strengths": "Strong visual matching skills, motivated by token economy",
    "areas_of_need": "Transitioning between activities, emotional regulation",
    "assessment_tools": "VB-MAPP, FBA, Clinical Observation",
    "created_at": "2024-01-01T08:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "session_form_data": {
    "pre_session_checklist": [
      {
        "id": "materials_prepared",
        "name": "Materials Prepared",
        "description": "Picture Cards, Tokens, Toys",
        "is_completed": false
      },
      {
        "id": "treatment_plan_reviewed",
        "name": "Treatment Plan Reviewed",
        "description": "Review plan: comprehensive_aba",
        "is_completed": false
      },
      {
        "id": "environment_setup",
        "name": "Environment Setup Complete",
        "description": "Quiet, distraction-free environment",
        "is_completed": false
      },
      {
        "id": "data_collection_ready",
        "name": "Data Collection Sheets Ready",
        "description": "Frequency counting for problem behavior, percentage correct for skill acquisition goals",
        "is_completed": false
      }
    ],
    "goals": [
      {
        "id": 1,
        "description": "Client will request help using PECS in 8/10 opportunities across 3 different activities",
        "mastery_criteria": "8/10_opportunities",
        "custom_mastery_criteria": "",
        "priority": "medium",
        "is_achieved": false,
        "progress_notes": ""
      },
      {
        "id": 2,
        "description": "Client will appropriately take turns in 3+ activities per session with peers",
        "mastery_criteria": "3+_activities_per_session",
        "custom_mastery_criteria": "",
        "priority": "high",
        "is_achieved": false,
        "progress_notes": ""
      }
    ],
    "suggested_activities": [
      {
        "id": "discrete_trial_training",
        "name": "Discrete Trial Training",
        "description": "Structured learning trials",
        "estimated_duration": 15
      },
      {
        "id": "natural_environment_training",
        "name": "Natural Environment Training",
        "description": "Learning in natural settings",
        "estimated_duration": 20
      },
      {
        "id": "social_skills_practice",
        "name": "Social Skills Practice",
        "description": "Peer interaction and social skills",
        "estimated_duration": 10
      }
    ],
    "reinforcement_strategies": [
      {
        "id": "token_economy",
        "name": "Token Economy",
        "description": "Token economy system, social praise, preferred items, break cards",
        "effectiveness_scale": "1-5"
      },
      {
        "id": "social_praise",
        "name": "Social Praise",
        "description": "Verbal and physical praise",
        "effectiveness_scale": "1-5"
      },
      {
        "id": "preferred_items",
        "name": "Preferred Items",
        "description": "Access to preferred activities/items",
        "effectiveness_scale": "1-5"
      }
    ],
    "intervention_strategies": {
      "prompting_hierarchy": "Least-to-most prompting: Independent -> Visual -> Gestural -> Verbal -> Physical",
      "behavior_interventions": "Antecedent interventions: visual schedules, first-then boards, choice offering. Consequence strategies: differential reinforcement, extinction, functional communication training",
      "reinforcement_strategies": "Token economy system, social praise, preferred items, break cards"
    },
    "data_collection_methods": "Frequency counting for problem behavior, percentage correct for skill acquisition goals, ABC data for antecedent-behavior-consequence analysis, duration data for engagement"
  }
}
```

### Ocean AI Dashboard Response
```json
{
  "session": {
    "id": 2,
    "client": "John Doe",
    "date": "2024-01-15",
    "start_time": "09:00:00",
    "end_time": "10:00:00",
    "status": "in_progress",
    "time_remaining_minutes": 15,
    "in_final_15_minutes": true
  },
  "ocean_integration": {
    "note_flow": {
      "is_note_completed": false,
      "final_note_submitted": false,
      "ai_generated_note": null,
      "rbt_reviewed": false
    },
    "prompts": {
      "total": 3,
      "responded": 2,
      "pending": 1,
      "list": [
        {
          "id": 1,
          "type": "engagement",
          "message": "How is the session going?",
          "response": "Going well, client is engaged",
          "is_responded": true,
          "created_at": "2024-01-15T09:15:00Z",
          "responded_at": "2024-01-15T09:16:00Z"
        }
      ]
    },
    "can_end_session": false,
    "blocking_reasons": [
      "Session note is not completed",
      "1 pending prompts need responses"
    ],
    "recommendations": [
      "Complete your session note to document today's progress",
      "Respond to 1 pending prompts"
    ]
  }
}
```

## 8. Error Responses

### 400 Bad Request
```json
{
  "error": "user_id parameter is required"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "error": "Only administrators can access user sessions"
}
```

### 404 Not Found
```json
{
  "error": "User not found"
}
```

## 9. Testing Workflow

1. **Login** to get JWT token
2. **Get sessions** to see available sessions
3. **Create session** if needed
4. **Start timer** for active session
5. **Add activities, goals, etc.** during session
6. **Generate AI notes** using Ocean AI
7. **Stop timer** and complete session
8. **View statistics** to see overall progress

## 10. Postman Collection Setup

1. Create a new collection called "Session API"
2. Set up environment variables:
   - `base_url`: `http://localhost:8000/sapphire/session`
   - `auth_token`: `{{your_jwt_token}}`
3. Add pre-request script to automatically include auth token:
```javascript
pm.request.headers.add({
    key: 'Authorization',
    value: 'Bearer ' + pm.environment.get('auth_token')
});
```

This comprehensive guide should help you test all aspects of the Session API effectively!
