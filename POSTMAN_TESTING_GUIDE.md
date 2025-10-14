# Postman Testing Guide for Session APIs

## 🚀 **Server Setup**
Your Django server should be running at: `http://localhost:8000`

## 🔐 **Authentication Setup**

### Step 1: Get JWT Token
First, you need to authenticate and get a JWT token.

**POST** `http://localhost:8000/api/auth/login/`
```json
{
  "email": "your_email@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Step 2: Set Authorization Header
In Postman, go to the **Authorization** tab and select **Bearer Token**, then paste your access token.

Or manually add to Headers:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

---

## 📋 **Session Logging APIs**

### 1. **Get All Sessions**
**GET** `http://localhost:8000/session/sessions/`

**Query Parameters (optional):**
- `status=scheduled`
- `start_date=2024-01-01`
- `end_date=2024-01-31`

---

### 2. **Create New Session**
**POST** `http://localhost:8000/session/sessions/`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN
```

**Body (JSON):**
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

---

### 3. **Get Session Details**
**GET** `http://localhost:8000/session/sessions/{session_id}/`

Replace `{session_id}` with actual ID from step 2.

---

### 4. **Start Session Timer**
**POST** `http://localhost:8000/session/sessions/{session_id}/timer/`

**Body (JSON):**
```json
{
  "action": "start"
}
```

**Response:**
```json
{
  "id": 1,
  "start_time": "2024-01-15T12:00:00Z",
  "end_time": null,
  "is_running": true,
  "total_duration": "00:00:00",
  "current_duration": "00:02:30"
}
```

---

### 5. **Stop Session Timer**
**POST** `http://localhost:8000/session/sessions/{session_id}/timer/`

**Body (JSON):**
```json
{
  "action": "stop"
}
```

---

### 6. **Add Activity**
**POST** `http://localhost:8000/session/sessions/{session_id}/activities/`

**Body (JSON):**
```json
{
  "activity_name": "Discrete Trial Training",
  "duration_minutes": 15,
  "reinforcement_strategies": "Picture Cards, Tokens",
  "notes": "Client appeared motivated and engaged during DTT session"
}
```

---

### 7. **Add ABC Event**
**POST** `http://localhost:8000/session/sessions/{session_id}/abc-events/`

**Body (JSON):**
```json
{
  "antecedent": "Asked to Clean Up",
  "behavior": "Refused to Comply",
  "consequence": "Sent to Time Out (briefly)"
}
```

---

### 8. **Add Goal Progress**
**POST** `http://localhost:8000/session/sessions/{session_id}/goal-progress/`

**Body (JSON):**
```json
{
  "goal_description": "Requesting Items",
  "is_met": true,
  "implementation_method": "verbal",
  "notes": "Client successfully requested items using verbal communication"
}
```

---

### 9. **Report Incident**
**POST** `http://localhost:8000/session/sessions/{session_id}/incidents/`

**Body (JSON):**
```json
{
  "incident_type": "sib",
  "behavior_severity": "critical",
  "start_time": "2024-01-15T12:00:00Z",
  "duration_minutes": 45,
  "description": "Client cried and threw toys when asked to clean up. He then began to hit his head with his left hand (SIB)."
}
```

---

### 10. **Submit Session**
**POST** `http://localhost:8000/session/sessions/submit/`

**Body (JSON):**
```json
{
  "session_id": 1,
  "submit_type": "submit"
}
```

---

## ⏰ **Time Tracker APIs**

### 1. **Get All Time Tracker Entries**
**GET** `http://localhost:8000/session/time-trackers/`

**Query Parameters (optional):**
- `session=1`
- `time_type=direct`
- `start_date=2024-01-01`
- `end_date=2024-01-31`

---

### 2. **Create Time Tracker Entry** (matches the form interface)
**POST** `http://localhost:8000/session/time-trackers/`

**Body (JSON):**
```json
{
  "session": 1,
  "time_type": "direct",
  "start_time": "2024-01-15T12:00:00Z",
  "end_time": "2024-01-15T13:00:00Z",
  "description": "Direct therapy session with client"
}
```

**Response:**
```json
{
  "id": 1,
  "session": 1,
  "time_type": "direct",
  "start_time": "2024-01-15T12:00:00Z",
  "end_time": "2024-01-15T13:00:00Z",
  "description": "Direct therapy session with client",
  "created_by": {
    "id": 1,
    "username": "therapist1",
    "email": "therapist@example.com",
    "role": "RBT"
  },
  "duration": 60.0,
  "duration_display": "01:00",
  "created_at": "2024-01-15T12:30:00Z",
  "updated_at": "2024-01-15T12:30:00Z"
}
```

---

### 3. **Get Time Tracker Details**
**GET** `http://localhost:8000/session/time-trackers/{id}/`

---

### 4. **Update Time Tracker Entry**
**PUT** `http://localhost:8000/session/time-trackers/{id}/`

**Body (JSON):**
```json
{
  "time_type": "supervision",
  "start_time": "2024-01-15T12:00:00Z",
  "end_time": "2024-01-15T13:30:00Z",
  "description": "Updated supervision session"
}
```

---

### 5. **Delete Time Tracker Entry**
**DELETE** `http://localhost:8000/session/time-trackers/{id}/`

---

### 6. **Get Time Tracker Summary**
**GET** `http://localhost:8000/session/time-trackers/summary/`

**Query Parameters (optional):**
- `start_date=2024-01-01`
- `end_date=2024-01-31`

**Response:**
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

---

## 📊 **Additional Endpoints**

### **Get Upcoming Sessions**
**GET** `http://localhost:8000/session/upcoming-sessions/`

### **Preview Session**
**GET** `http://localhost:8000/session/sessions/preview/`

**Body (JSON):**
```json
{
  "session_id": 1
}
```

---

## 🧪 **Testing Workflow**

### **Complete Session Flow:**
1. **Login** → Get JWT token
2. **Create Session** → Get session ID
3. **Start Timer** → Begin session timing
4. **Add Activities** → Log session activities
5. **Add ABC Events** → Record behaviors
6. **Add Goal Progress** → Track goals
7. **Stop Timer** → End session timing
8. **Submit Session** → Complete session

### **Time Tracker Flow:**
1. **Create Time Tracker Entry** → Log manual time
2. **View Time Tracker Entries** → See all entries
3. **Get Summary** → View statistics

---

## ⚠️ **Common Issues & Solutions**

### **401 Unauthorized**
- Check if JWT token is valid
- Ensure Authorization header is set correctly
- Try refreshing the token

### **403 Forbidden**
- Check user permissions/role
- Ensure user has access to the session

### **400 Bad Request**
- Check JSON format
- Verify required fields are provided
- Check date/time format (ISO 8601)

### **404 Not Found**
- Verify the endpoint URL
- Check if the resource ID exists

---

## 📝 **Postman Collection Setup**

### **Environment Variables:**
Create a Postman environment with:
- `base_url`: `http://localhost:8000`
- `token`: `{{your_jwt_token}}`

### **Pre-request Script:**
Add to collection level:
```javascript
pm.request.headers.add({
    key: 'Authorization',
    value: 'Bearer ' + pm.environment.get('token')
});
```

This guide will help you test all the session logging and time tracking APIs in Postman! 🎯
