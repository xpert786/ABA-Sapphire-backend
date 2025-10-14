# Session Logging API Documentation

This document provides comprehensive information about the Session Logging APIs created for the Sapphire therapy session management system.

## Base URL
All session APIs are available under: `http://your-domain/session/`

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## API Endpoints

### 1. Session Management

#### Get All Sessions
- **GET** `/session/sessions/`
- **Description**: Retrieve all sessions for the authenticated user
- **Query Parameters**:
  - `status` (optional): Filter by session status (`scheduled`, `in_progress`, `completed`, `cancelled`)
  - `start_date` (optional): Filter sessions from this date (YYYY-MM-DD)
  - `end_date` (optional): Filter sessions until this date (YYYY-MM-DD)
- **Response**: List of session objects with basic information

#### Get Session Details
- **GET** `/session/sessions/{id}/`
- **Description**: Retrieve detailed information about a specific session including all related data
- **Response**: Complete session object with all form data

#### Create New Session
- **POST** `/session/sessions/`
- **Description**: Create a new therapy session
- **Request Body**:
```json
{
  "client": 1,
  "session_date": "2024-01-15",
  "start_time": "12:00:00",
  "end_time": "13:00:00",
  "location": "123 ABA Street, Building 1, Room 201",
  "service_type": "ABA"
}
```

#### Update Session
- **PUT/PATCH** `/session/sessions/{id}/`
- **Description**: Update session information

#### Delete Session
- **DELETE** `/session/sessions/{id}/`

#### Get Upcoming Sessions
- **GET** `/session/upcoming-sessions/`
- **Description**: Get all upcoming sessions (today and future) for the authenticated user

### 2. Session Timer

#### Get Timer Status
- **GET** `/session/sessions/{session_id}/timer/`
- **Description**: Get current timer status for a session
- **Response**:
```json
{
  "id": 1,
  "start_time": "2024-01-15T12:00:00Z",
  "end_time": null,
  "is_running": true,
  "total_duration": "00:15:30",
  "current_duration": "00:15:30"
}
```

#### Start/Stop Timer
- **POST** `/session/sessions/{session_id}/timer/`
- **Description**: Start or stop the session timer
- **Request Body**:
```json
{
  "action": "start"  // or "stop"
}
```

### 3. Additional Time Management

#### Get Additional Time Entries
- **GET** `/session/sessions/{session_id}/additional-time/`
- **Description**: Get all additional time entries for a session

#### Add Additional Time
- **POST** `/session/sessions/{session_id}/additional-time/`
- **Description**: Add additional time entry
- **Request Body**:
```json
{
  "time_type": "direct",
  "duration": 15,
  "unit": "minutes",
  "reason": "Client needed extra support during transition"
}
```

### 4. Pre-Session Checklist

#### Get Checklist Items
- **GET** `/session/sessions/{session_id}/checklist/`
- **Description**: Get all checklist items for a session

#### Add Checklist Item
- **POST** `/session/sessions/{session_id}/checklist/`
- **Description**: Add or update checklist item
- **Request Body**:
```json
{
  "item_name": "Materials Required",
  "is_completed": true,
  "notes": "Picture Cards, Tokens, Toys ready"
}
```

### 5. Activities Management

#### Get Session Activities
- **GET** `/session/sessions/{session_id}/activities/`
- **Description**: Get all activities for a session

#### Add Activity
- **POST** `/session/sessions/{session_id}/activities/`
- **Description**: Add a new activity
- **Request Body**:
```json
{
  "activity_name": "Discrete Trial Training",
  "duration_minutes": 15,
  "reinforcement_strategies": "Picture Cards, Tokens",
  "notes": "Client appeared motivated and engaged during DTT session"
}
```

### 6. Reinforcement Strategies

#### Get Reinforcement Strategies
- **GET** `/session/sessions/{session_id}/reinforcement-strategies/`
- **Description**: Get all reinforcement strategies used in session

#### Add Reinforcement Strategy
- **POST** `/session/sessions/{session_id}/reinforcement-strategies/`
- **Description**: Add a new reinforcement strategy
- **Request Body**:
```json
{
  "strategy_type": "Token Economy",
  "frequency": 15,
  "pr_ratio": 90,
  "notes": "Client responded to tokens, verbally, 100% of session"
}
```

### 7. ABC Events (Antecedent-Behavior-Consequence)

#### Get ABC Events
- **GET** `/session/sessions/{session_id}/abc-events/`
- **Description**: Get all ABC events recorded for the session

#### Add ABC Event
- **POST** `/session/sessions/{session_id}/abc-events/`
- **Description**: Record a new ABC event
- **Request Body**:
```json
{
  "antecedent": "Asked to Clean Up",
  "behavior": "Refused to Comply",
  "consequence": "Sent to Time Out (briefly)"
}
```

### 8. Goal Progress Tracking

#### Get Goal Progress
- **GET** `/session/sessions/{session_id}/goal-progress/`
- **Description**: Get all goal progress entries for the session

#### Add Goal Progress
- **POST** `/session/sessions/{session_id}/goal-progress/`
- **Description**: Record goal progress
- **Request Body**:
```json
{
  "goal_description": "Requesting Items",
  "is_met": true,
  "implementation_method": "verbal",
  "notes": "Client successfully requested items using verbal communication"
}
```

### 9. Incidents & Crisis Management

#### Get Incidents
- **GET** `/session/sessions/{session_id}/incidents/`
- **Description**: Get all incidents recorded for the session

#### Report Incident
- **POST** `/session/sessions/{session_id}/incidents/`
- **Description**: Report an incident or crisis
- **Request Body**:
```json
{
  "incident_type": "sib",
  "behavior_severity": "critical",
  "start_time": "2024-01-15T12:00:00Z",
  "duration_minutes": 45,
  "description": "Client cried and threw toys when asked to clean up. He then began to hit his head with his left hand (SIB). He stopped once staff redirected."
}
```

### 10. Session Notes

#### Get Session Notes
- **GET** `/session/sessions/{session_id}/notes/`
- **Description**: Get all notes for the session

#### Add Session Note
- **POST** `/session/sessions/{session_id}/notes/`
- **Description**: Add a general session note
- **Request Body**:
```json
{
  "note_content": "Overall session went well. Client showed good progress in communication goals.",
  "note_type": "general"
}
```

### 11. Session Actions

#### Submit Session
- **POST** `/session/sessions/submit/`
- **Description**: Submit or save session as draft
- **Request Body**:
```json
{
  "session_id": 1,
  "submit_type": "submit"  // or "draft"
}
```

#### Preview Session
- **GET** `/session/sessions/preview/`
- **Description**: Preview complete session data before submission
- **Request Body**:
```json
{
  "session_id": 1
}
```

### 12. Time Tracker Management

#### Get Time Tracker Entries
- **GET** `/session/time-trackers/`
- **Description**: Get all time tracker entries for the authenticated user
- **Query Parameters**:
  - `session` (optional): Filter by session ID
  - `time_type` (optional): Filter by time type (`direct`, `indirect`, `supervision`, `documentation`, `travel`, `training`, `meeting`)
  - `start_date` (optional): Filter entries from this date (YYYY-MM-DD)
  - `end_date` (optional): Filter entries until this date (YYYY-MM-DD)
- **Response**: List of time tracker entries with duration calculations

#### Create Time Tracker Entry
- **POST** `/session/time-trackers/`
- **Description**: Create a new time tracker entry (matches the "Add time tracker" form)
- **Request Body**:
```json
{
  "session": 1,
  "time_type": "direct",
  "start_time": "2024-01-15T12:00:00Z",
  "end_time": "2024-01-15T13:00:00Z",
  "description": "Direct therapy session with client"
}
```

#### Get Time Tracker Details
- **GET** `/session/time-trackers/{id}/`
- **Description**: Get detailed information about a specific time tracker entry
- **Response**: Complete time tracker object with calculated duration

#### Update Time Tracker Entry
- **PUT/PATCH** `/session/time-trackers/{id}/`
- **Description**: Update an existing time tracker entry
- **Request Body**:
```json
{
  "time_type": "supervision",
  "start_time": "2024-01-15T12:00:00Z",
  "end_time": "2024-01-15T13:30:00Z",
  "description": "Supervision session updated"
}
```

#### Delete Time Tracker Entry
- **DELETE** `/session/time-trackers/{id}/`
- **Description**: Delete a time tracker entry

#### Get Time Tracker Summary
- **GET** `/session/time-trackers/summary/`
- **Description**: Get summary statistics for time tracker entries
- **Query Parameters**:
  - `start_date` (optional): Filter summary from this date
  - `end_date` (optional): Filter summary until this date
- **Response**:
```json
{
  "total_entries": 25,
  "total_duration_minutes": 1500,
  "total_duration_hours": 25.0,
  "total_duration_display": "25:00",
  "time_type_summary": {
    "direct": {
      "count": 15,
      "total_duration": 900,
      "display_name": "Direct Therapy"
    },
    "supervision": {
      "count": 5,
      "total_duration": 300,
      "display_name": "Supervision"
    }
  }
}
```

## Data Models

### Session Status Choices
- `scheduled`: Session is planned
- `in_progress`: Session is currently active
- `completed`: Session has been completed
- `cancelled`: Session was cancelled

### Time Type Choices
- `direct`: Direct therapy time
- `indirect`: Indirect therapy time
- `supervision`: Supervision time

### Unit Choices
- `minutes`: Time in minutes
- `hours`: Time in hours

### Incident Type Choices
- `sib`: SIB/Self-Injurious Behavior
- `aggression`: Aggression
- `elopement`: Elopement
- `major_disruption`: Major Disruption
- `minor_disruption`: Minor Disruption
- `odr`: ODR
- `ir`: IR
- `crisis`: CRISIS

### Behavior Severity Choices
- `low`: Low severity
- `moderate`: Moderate severity
- `high`: High severity
- `critical`: Critical severity

### Implementation Method Choices
- `verbal`: Verbal implementation
- `visual`: Visual implementation
- `physical`: Physical implementation
- `combination`: Combination of methods

### Time Tracker Type Choices
- `direct`: Direct Therapy
- `indirect`: Indirect Therapy
- `supervision`: Supervision
- `documentation`: Documentation
- `travel`: Travel Time
- `training`: Training
- `meeting`: Meeting

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a JSON object with error details:
```json
{
  "error": "Error message description",
  "details": "Additional error details if available"
}
```

## Role-Based Access Control

- **RBT/BCBA**: Can manage sessions they are assigned to
- **Clients/Parent**: Can view their own sessions
- **Admin**: Can access all sessions

## Usage Examples

### Complete Session Flow
1. Create a session: `POST /session/sessions/`
2. Start timer: `POST /session/sessions/{id}/timer/` with `{"action": "start"}`
3. Add activities, ABC events, etc. as needed
4. Stop timer: `POST /session/sessions/{id}/timer/` with `{"action": "stop"}`
5. Submit session: `POST /session/sessions/submit/` with `{"session_id": id, "submit_type": "submit"}`

### Bulk Data Entry
You can add multiple items of the same type by making multiple POST requests to the respective endpoints for each session form section.

### Time Tracker Usage Examples

#### Add Time Tracker Entry (matches the form interface)
1. Create a time tracker entry: `POST /session/time-trackers/` with session, start/end times
2. View time tracker entries: `GET /session/time-trackers/`
3. Get summary statistics: `GET /session/time-trackers/summary/`

#### Time Tracker Form Integration
The API endpoints directly support the "Add time tracker" form interface:
- Session selection dropdown
- Start time (date + time)
- End time (date + time)
- Time type selection
- Description field
- Save actions (Save, Save and add another, Save and continue editing)

This API provides complete functionality for managing therapy session logging and time tracking as shown in the interfaces, with proper authentication, authorization, and data validation.
