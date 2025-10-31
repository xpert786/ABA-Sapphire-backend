# Scheduler Sessions API - Treatment Plan Integration Guide

## 🎯 Overview

This guide explains how to use the new **Treatment Plan ID** feature in the Sessions API. When you provide a `treatment_plan_id` when creating a session, the system automatically selects the correct client based on the treatment plan's client information.

## 🚀 New Features

### 1. **Automatic Client Selection**
   - When creating a session with `treatment_plan_id`, the client is automatically selected
   - The system matches the treatment plan's `client_id` or `client_name` to find the corresponding user
   - No need to manually specify the client anymore!

### 2. **Filter Sessions by Treatment Plan**
   - Query parameter `?treatment_plan_id=1` to filter sessions for a specific treatment plan
   - Easy to see all sessions scheduled for a particular treatment plan

## 📋 Postman Collection Setup

### Step 1: Import the Collection
1. Open Postman
2. Click **Import** button (top left)
3. Select the file: `SCHEDULER_SESSIONS_POSTMAN_COLLECTION.json`
4. Click **Import**

### Step 2: Configure Environment Variables
1. Click on **Environments** (left sidebar)
2. Create a new environment or use the default
3. Set the following variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `base_url` | `http://localhost:8000` | Your server URL |
| `auth_token` | `YOUR_JWT_TOKEN` | Your authentication token |
| `session_id` | `1` | Example session ID for testing |
| `treatment_plan_id` | `1` | Example treatment plan ID |

## 📝 API Endpoints

### Base URL
```
{{base_url}}/sapphire/scheduler/sessions/
```

### Authentication
All endpoints require JWT authentication:
```
Authorization: Bearer {{auth_token}}
```

---

## 🔥 Main Features

### 1. Create Session with Treatment Plan ID (NEW!)

**Endpoint:** `POST /sapphire/scheduler/sessions/`

**Request Body:**
```json
{
    "treatment_plan_id": 1,
    "session_date": "2025-01-20",
    "start_time": "10:00:00",
    "end_time": "11:00:00",
    "staff": 2,
    "session_notes": "Initial session with treatment plan integration"
}
```

**Key Points:**
- ✅ **NO `client` field needed!** The system automatically finds the client
- ✅ The client is matched using the treatment plan's `client_id` or `client_name`
- ✅ Matching tries multiple strategies:
  1. Username match
  2. Staff ID match
  3. Numeric ID match
  4. Name partial match

**Success Response (201):**
```json
{
    "id": 123,
    "client": 5,
    "staff": 2,
    "treatment_plan": 1,
    "session_date": "2025-01-20",
    "start_time": "10:00:00",
    "end_time": "11:00:00",
    "session_notes": "Initial session with treatment plan integration",
    "client_details": {
        "id": 5,
        "name": "John Doe",
        "username": "john.doe"
    },
    "staff_details": {
        "id": 2,
        "name": "Jane Smith",
        "username": "jane.smith"
    }
}
```

**Error Response (400):**
```json
{
    "treatment_plan_id": [
        "Could not find a client user matching treatment plan client_id \"CLIENT001\" or client_name \"John Doe\". Please specify client manually."
    ]
}
```

---

### 2. Create Session without Treatment Plan (Manual Method)

**Request Body:**
```json
{
    "client": 3,
    "session_date": "2025-01-21",
    "start_time": "14:00:00",
    "end_time": "15:00:00",
    "staff": 2,
    "session_notes": "Manual session creation"
}
```

**Note:** This is the traditional method - still works if you prefer manual client selection.

---

### 3. List All Sessions

**Endpoint:** `GET /sapphire/scheduler/sessions/`

**Response:**
- Returns all upcoming sessions (including today) for the logged-in staff
- Ordered by session_date and start_time (ascending)

**Query Parameters:**
- None required
- Only returns sessions where `staff` matches the logged-in user

---

### 4. Filter Sessions by Treatment Plan ID (NEW!)

**Endpoint:** `GET /sapphire/scheduler/sessions/?treatment_plan_id=1`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `treatment_plan_id` | integer | No | Filter sessions by treatment plan ID |

**Example:**
```bash
GET {{base_url}}/sapphire/scheduler/sessions/?treatment_plan_id=1
```

**Use Case:**
- View all sessions scheduled for a specific treatment plan
- Track progress across multiple sessions for one treatment plan
- Generate reports for treatment plan effectiveness

---

### 5. Get Session Detail

**Endpoint:** `GET /sapphire/scheduler/sessions/{id}/`

**Response:**
```json
{
    "id": 123,
    "client": 5,
    "staff": 2,
    "treatment_plan": 1,
    "session_date": "2025-01-20",
    "start_time": "10:00:00",
    "end_time": "11:00:00",
    "session_notes": "Session notes...",
    "duration": null,
    "created_at": "2025-01-15T10:00:00Z",
    "client_details": { ... },
    "staff_details": { ... }
}
```

---

### 6. Update Session

**Endpoint:** `PATCH /sapphire/scheduler/sessions/{id}/`

**Request Body (Partial Update):**
```json
{
    "session_notes": "Updated notes",
    "start_time": "10:30:00"
}
```

**Note:** You can update individual fields without sending all data.

---

### 7. Delete Session

**Endpoint:** `DELETE /sapphire/scheduler/sessions/{id}/`

**Response:** 204 No Content

---

## 🔍 Client Matching Logic

When `treatment_plan_id` is provided, the system tries to find the client user in this order:

1. **Username Match:** `CustomUser.objects.get(username=treatment_plan.client_id)`
2. **Staff ID Match:** `CustomUser.objects.get(staff_id=treatment_plan.client_id)`
3. **Numeric ID Match:** `CustomUser.objects.get(id=treatment_plan.client_id)` (if client_id is numeric)
4. **Name Partial Match:** `CustomUser.objects.filter(name__icontains=treatment_plan.client_name)`

**Important:** The user must have role `'Clients/Parent'` to be matched.

---

## 📊 Example Workflows

### Workflow 1: Create Session from Treatment Plan
```
1. GET /treatment-plan/treatment-plans/ → Find treatment plan ID
2. POST /scheduler/sessions/ → Create session with treatment_plan_id
3. GET /scheduler/sessions/?treatment_plan_id=1 → View all sessions for this plan
```

### Workflow 2: Track Treatment Plan Progress
```
1. GET /scheduler/sessions/?treatment_plan_id=1 → Get all sessions
2. Analyze session completion and outcomes
3. Update treatment plan based on progress
```

---

## 🧪 Testing Checklist

- [ ] Create session with valid `treatment_plan_id`
- [ ] Verify client is automatically selected
- [ ] Create session with invalid `treatment_plan_id` (should error)
- [ ] Create session with `treatment_plan_id` that has no matching client (should error)
- [ ] Filter sessions by `treatment_plan_id` query parameter
- [ ] List all sessions without filter
- [ ] Update session details
- [ ] Delete session

---

## ⚠️ Error Handling

### Treatment Plan Not Found
```json
{
    "treatment_plan_id": ["Treatment plan not found."]
}
```

### Client Not Found for Treatment Plan
```json
{
    "treatment_plan_id": [
        "Could not find a client user matching treatment plan client_id \"XYZ\" or client_name \"John Doe\". Please specify client manually."
    ]
}
```

### Missing Required Fields
```json
{
    "session_date": ["This field is required."],
    "start_time": ["This field is required."],
    "end_time": ["This field is required."]
}
```

---

## 🔍 How to Find Client ID from Treatment Plan

**This answers your question: "If I select treatment plan, how to know client ID?"**

### New Helper Endpoint

**Endpoint:** `GET /sapphire/treatment-plan/plans/{treatment_plan_id}/client/`

**Description:** 
Get the client ID and information that will be automatically selected when creating a session with this treatment_plan_id.

**Example Request:**
```bash
GET {{base_url}}/sapphire/treatment-plan/plans/1/client/
Authorization: Bearer {{auth_token}}
```

**Success Response (200):**
```json
{
    "treatment_plan": {
        "id": 1,
        "client_name": "John Doe",
        "client_id": "CLIENT001",
        "plan_type": "Comprehensive ABA"
    },
    "matched_client": {
        "id": 5,
        "username": "john.doe",
        "name": "John Doe",
        "email": "john@example.com",
        "staff_id": "STAFF0005",
        "role": "Clients/Parent"
    },
    "matching_method": "username",
    "message": "Client found! Use client ID 5 or simply use treatment_plan_id when creating a session."
}
```

**Error Response (404) - Client Not Found:**
```json
{
    "treatment_plan": {
        "id": 1,
        "client_name": "John Doe",
        "client_id": "CLIENT999"
    },
    "matched_client": null,
    "error": "Could not find a client user matching treatment plan client_id \"CLIENT999\" or client_name \"John Doe\".",
    "suggestion": "Please create the client user first or verify the client_id/client_name in the treatment plan matches an existing user."
}
```

**Use Cases:**
1. **Before creating a session** - Verify which client will be selected
2. **UI Development** - Display client info when user selects a treatment plan
3. **Validation** - Check if client exists before attempting to create session
4. **Debugging** - Understand which client matching method was used

**Workflow:**
```
1. User selects treatment plan ID = 1
2. Call GET /treatment-plan/plans/1/client/
3. Response shows matched_client.id = 5
4. Now you know the client ID!
5. Create session with treatment_plan_id=1 (client auto-selected)
   OR create session with client=5 manually
```

---

## 🔗 Related Endpoints

### Treatment Plans
- `GET /sapphire/treatment-plan/treatment-plans/` - List all treatment plans
- `GET /sapphire/treatment-plan/treatment-plans/{id}/` - Get treatment plan details
- `GET /sapphire/treatment-plan/plans/{id}/client/` - **NEW!** Get client ID from treatment plan

### Clients
- `GET /sapphire/scheduler/clients/` - List all clients

---

## 📞 Support

For issues or questions:
1. Check the error response for detailed messages
2. Verify treatment plan exists and has valid client_id/client_name
3. Ensure client user exists with role 'Clients/Parent'
4. Verify authentication token is valid

---

## 🎉 Benefits of New Feature

1. **Simplified Session Creation:** No need to look up client ID separately
2. **Data Consistency:** Ensures sessions are linked to correct treatment plans
3. **Better Tracking:** Filter and analyze sessions by treatment plan
4. **Reduced Errors:** Automatic matching reduces manual data entry mistakes
5. **Improved Workflow:** Streamlined process for BCBAs creating sessions

---

**Last Updated:** January 2025  
**API Version:** v1.0  
**Collection Version:** 1.0

