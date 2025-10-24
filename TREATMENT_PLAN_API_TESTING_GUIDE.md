# Treatment Plan API Testing Guide

This guide provides comprehensive examples for testing the Treatment Plan API using both Postman and curl commands.

## Base URL
```
http://localhost:8000/sapphire/treatment-plan/
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

## 2. Treatment Plan Endpoints

### 2.1 Create a New Treatment Plan

```bash
curl -X POST http://localhost:8000/sapphire/treatment-plan/plans/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "client_name": "John Doe",
    "client_id": "4",
    "bcba": 6,
    "assessment_tools_used": "VB-MAPP, FBA, Clinical Observation",
    "client_strengths": "Strong visual matching skills, motivated by token economy, responds well to social praise",
    "areas_of_need": "Transitioning between activities, emotional regulation, social skills, functional communication",
    "reinforcement_strategies": "Token economy system, social praise, preferred items, break cards",
    "prompting_hierarchy": "Least-to-most prompting: Independent -> Visual -> Gestural -> Verbal -> Physical",
    "behavior_interventions": "Antecedent interventions: visual schedules, first-then boards, choice offering. Consequence strategies: differential reinforcement, extinction, functional communication training",
    "data_collection_methods": "Frequency counting for problem behavior, percentage correct for skill acquisition goals, ABC data for antecedent-behavior-consequence analysis, duration data for engagement",
    "priority": "medium",
    "goals": [
      {
        "goal_description": "Client will request help using PECS in 8/10 opportunities across 3 different activities",
        "mastery_criteria": "8/10_opportunities",
        "priority": "medium"
      },
      {
        "goal_description": "Client will appropriately take turns in 3+ activities per session with peers",
        "mastery_criteria": "3+_activities_per_session",
        "priority": "high"
      },
      {
        "goal_description": "Client will follow 1-step directions with 80% accuracy across 2 consecutive sessions",
        "mastery_criteria": "80%_accuracy",
        "priority": "medium"
      }
    ]
  }'
```

**Postman:**
- Method: POST
- URL: `http://localhost:8000/sapphire/treatment-plan/plans/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <your_access_token>`
- Body (raw JSON): [Same JSON as above]

### 2.2 Get All Treatment Plans

```bash
curl -X GET http://localhost:8000/sapphire/treatment-plan/plans/ \
  -H "Authorization: Bearer <your_access_token>"
```

**With Query Parameters:**
```bash
# Filter by status
curl -X GET "http://localhost:8000/sapphire/treatment-plan/plans/?status=draft" \
  -H "Authorization: Bearer <your_access_token>"

# Filter by priority
curl -X GET "http://localhost:8000/sapphire/treatment-plan/plans/?priority=high" \
  -H "Authorization: Bearer <your_access_token>"

# Search by client name or ID
curl -X GET "http://localhost:8000/sapphire/treatment-plan/plans/?search=John" \
  -H "Authorization: Bearer <your_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/treatment-plan/plans/`
- Headers: `Authorization: Bearer <your_access_token>`
- Query Params (optional):
  - `status`: draft, submitted, approved, rejected
  - `priority`: low, medium, high
  - `search`: client name or ID

### 2.3 Get Specific Treatment Plan

```bash
curl -X GET http://localhost:8000/sapphire/treatment-plan/plans/1/ \
  -H "Authorization: Bearer <your_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/treatment-plan/plans/1/`
- Headers: `Authorization: Bearer <your_access_token>`

### 2.4 Update Treatment Plan

```bash
curl -X PUT http://localhost:8000/sapphire/treatment-plan/plans/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "client_name": "John Doe Updated",
    "client_id": "CLIENT001",
    "bcba": 1,
    "assessment_tools_used": "VB-MAPP, FBA, Clinical Observation, ADOS-2",
    "client_strengths": "Strong visual matching skills, motivated by token economy, responds well to social praise, excellent memory",
    "areas_of_need": "Transitioning between activities, emotional regulation, social skills, functional communication",
    "reinforcement_strategies": "Token economy system, social praise, preferred items, break cards",
    "prompting_hierarchy": "Least-to-most prompting: Independent -> Visual -> Gestural -> Verbal -> Physical",
    "behavior_interventions": "Antecedent interventions: visual schedules, first-then boards, choice offering. Consequence strategies: differential reinforcement, extinction, functional communication training",
    "data_collection_methods": "Frequency counting for problem behavior, percentage correct for skill acquisition goals, ABC data for antecedent-behavior-consequence analysis, duration data for engagement",
    "priority": "high",
    "status": "draft"
  }'
```

**Postman:**
- Method: PUT
- URL: `http://localhost:8000/sapphire/treatment-plan/plans/1/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <your_access_token>`
- Body (raw JSON): [Updated JSON data]

### 2.5 Submit Treatment Plan for Approval

```bash
curl -X POST http://localhost:8000/sapphire/treatment-plan/plans/1/submit/ \
  -H "Authorization: Bearer <your_access_token>"
```

**Postman:**
- Method: POST
- URL: `http://localhost:8000/sapphire/treatment-plan/plans/1/submit/`
- Headers: `Authorization: Bearer <your_access_token>`

### 2.6 Approve/Reject Treatment Plan (Admin Only)

```bash
# Approve
curl -X POST http://localhost:8000/sapphire/treatment-plan/plans/1/approve/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_access_token>" \
  -d '{
    "approved": true,
    "approval_notes": "Plan looks comprehensive and well-structured. Approved for implementation."
  }'

# Reject
curl -X POST http://localhost:8000/sapphire/treatment-plan/plans/1/approve/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_access_token>" \
  -d '{
    "approved": false,
    "approval_notes": "Needs more specific data collection methods and clearer mastery criteria."
  }'
```

**Postman:**
- Method: POST
- URL: `http://localhost:8000/sapphire/treatment-plan/plans/1/approve/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <admin_access_token>`
- Body (raw JSON):
```json
{
  "approved": true,
  "approval_notes": "Plan looks comprehensive and well-structured. Approved for implementation."
}
```

### 2.7 Get Treatment Plan Statistics

```bash
curl -X GET http://localhost:8000/sapphire/treatment-plan/plans/stats/ \
  -H "Authorization: Bearer <your_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/treatment-plan/plans/stats/`
- Headers: `Authorization: Bearer <your_access_token>`

## 3. Treatment Goals Endpoints

### 3.1 Get Goals for a Treatment Plan

```bash
curl -X GET http://localhost:8000/sapphire/treatment-plan/plans/1/goals/ \
  -H "Authorization: Bearer <your_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/treatment-plan/plans/1/goals/`
- Headers: `Authorization: Bearer <your_access_token>`

### 3.2 Create a New Goal

```bash
curl -X POST http://localhost:8000/sapphire/treatment-plan/plans/1/goals/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "goal_description": "Client will independently complete morning routine with 90% accuracy",
    "mastery_criteria": "90%_accuracy",
    "priority": "high",
    "progress_notes": "Initial baseline shows 60% accuracy"
  }'
```

**Postman:**
- Method: POST
- URL: `http://localhost:8000/sapphire/treatment-plan/plans/1/goals/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <your_access_token>`
- Body (raw JSON): [Goal data as above]

### 3.3 Update a Goal

```bash
curl -X PUT http://localhost:8000/sapphire/treatment-plan/plans/1/goals/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "goal_description": "Client will request help using PECS in 8/10 opportunities across 3 different activities",
    "mastery_criteria": "8/10_opportunities",
    "priority": "high",
    "is_achieved": true,
    "progress_notes": "Goal achieved on 2024-01-15. Client now consistently requests help using PECS."
  }'
```

**Postman:**
- Method: PUT
- URL: `http://localhost:8000/sapphire/treatment-plan/plans/1/goals/1/`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <your_access_token>`
- Body (raw JSON): [Updated goal data]

### 3.4 Delete a Goal

```bash
curl -X DELETE http://localhost:8000/sapphire/treatment-plan/plans/1/goals/1/ \
  -H "Authorization: Bearer <your_access_token>"
```

**Postman:**
- Method: DELETE
- URL: `http://localhost:8000/sapphire/treatment-plan/plans/1/goals/1/`
- Headers: `Authorization: Bearer <your_access_token>`

## 4. Approval Endpoints

### 4.1 Get All Approvals (Admin Only)

```bash
curl -X GET http://localhost:8000/sapphire/treatment-plan/approvals/ \
  -H "Authorization: Bearer <admin_access_token>"
```

**Postman:**
- Method: GET
- URL: `http://localhost:8000/sapphire/treatment-plan/approvals/`
- Headers: `Authorization: Bearer <admin_access_token>`

## 5. Sample Response Formats

### Treatment Plan Response
```json
{
  "id": 1,
  "client_name": "John Doe",
  "client_id": "CLIENT001",
  "bcba": 1,
  "bcba_name": "Dr. Jane Smith",
  "bcba_email": "jane.smith@example.com",
  "assessment_tools_used": "VB-MAPP, FBA, Clinical Observation",
  "client_strengths": "Strong visual matching skills, motivated by token economy, responds well to social praise",
  "areas_of_need": "Transitioning between activities, emotional regulation, social skills, functional communication",
  "reinforcement_strategies": "Token economy system, social praise, preferred items, break cards",
  "prompting_hierarchy": "Least-to-most prompting: Independent -> Visual -> Gestural -> Verbal -> Physical",
  "behavior_interventions": "Antecedent interventions: visual schedules, first-then boards, choice offering. Consequence strategies: differential reinforcement, extinction, functional communication training",
  "data_collection_methods": "Frequency counting for problem behavior, percentage correct for skill acquisition goals, ABC data for antecedent-behavior-consequence analysis, duration data for engagement",
  "status": "draft",
  "priority": "medium",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "submitted_at": null,
  "approved_at": null,
  "goals": [
    {
      "id": 1,
      "goal_description": "Client will request help using PECS in 8/10 opportunities across 3 different activities",
      "mastery_criteria": "8/10_opportunities",
      "custom_mastery_criteria": null,
      "priority": "medium",
      "is_achieved": false,
      "achieved_date": null,
      "progress_notes": "",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "goals_count": 3
}
```

### Statistics Response
```json
{
  "total_plans": 15,
  "draft_plans": 5,
  "submitted_plans": 3,
  "approved_plans": 6,
  "rejected_plans": 1,
  "high_priority_plans": 4,
  "medium_priority_plans": 8,
  "low_priority_plans": 3
}
```

## 6. Error Responses

### 400 Bad Request
```json
{
  "error": "Only draft treatment plans can be submitted for approval."
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
  "error": "You don't have permission to submit this treatment plan."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

## 7. Testing Workflow

1. **Login** to get JWT token
2. **Create** a treatment plan with goals
3. **View** the created plan
4. **Update** the plan if needed
5. **Submit** the plan for approval
6. **Login as admin** to approve/reject
7. **View statistics** to see overall status

## 8. Postman Collection Setup

1. Create a new collection called "Treatment Plan API"
2. Set up environment variables:
   - `base_url`: `http://localhost:8000/sapphire/treatment-plan`
   - `auth_token`: `{{your_jwt_token}}`
3. Add pre-request script to automatically include auth token:
```javascript
pm.request.headers.add({
    key: 'Authorization',
    value: 'Bearer ' + pm.environment.get('auth_token')
});
```

This comprehensive guide should help you test all aspects of the Treatment Plan API effectively!
