# Ocean AI RBT Session Note Flow - Postman Testing Guide

## 🚀 Complete cURL Commands for Testing

### **Prerequisites**
- Replace `{session_id}` with actual session ID (e.g., `123`)
- Replace `{prompt_id}` with actual prompt ID (e.g., `456`)
- Replace `{base_url}` with your server URL (e.g., `http://localhost:8000`)
- Add authentication headers as needed

---

## 📊 **1. Session Dashboard with Ocean AI**

### Get Complete Session Dashboard
```bash
curl -X GET "{base_url}/api/sessions/{session_id}/ocean-dashboard/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "session": {
    "id": 123,
    "client": "Sophia M.",
    "date": "2024-01-15",
    "start_time": "10:00:00",
    "end_time": "12:00:00",
    "status": "in_progress",
    "time_remaining_minutes": 45,
    "in_final_15_minutes": false
  },
  "ocean_integration": {
    "note_flow": {
      "is_note_completed": false,
      "final_note_submitted": false,
      "ai_generated_note": null,
      "rbt_reviewed": false
    },
    "prompts": {
      "total": 2,
      "responded": 1,
      "pending": 1,
      "list": [...]
    },
    "can_end_session": false,
    "blocking_reasons": ["Session note is not completed"],
    "recommendations": ["Complete your session note to document today's progress"]
  }
}
```

---

## 🤖 **2. Ocean AI Prompting System**

### Create Engagement Prompt
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-prompt/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_type": "engagement"
  }'
```

### Create Goal Check Prompt
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-prompt/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_type": "goal_check"
  }'
```

### Create Behavior Tracking Prompt
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-prompt/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_type": "behavior_tracking"
  }'
```

### Create Session Wrap Prompt (15-minute warning)
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-prompt/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_type": "session_wrap"
  }'
```

**Expected Response:**
```json
{
  "prompt": {
    "id": 456,
    "type": "engagement",
    "message": "How is the session going? Are you hitting your targets today?",
    "is_responded": false,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "Ocean prompt created successfully"
}
```

---

## 💬 **3. Respond to Ocean Prompts**

### Respond to Engagement Prompt
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-prompt/{prompt_id}/respond/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "Session is going well! Client is engaged and we are hitting our targets. Client completed 8/10 trials successfully."
  }'
```

### Respond to Goal Check Prompt
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-prompt/{prompt_id}/respond/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "Great progress on requesting help - achieved 86% today. Some regression noted but overall positive trend."
  }'
```

### Respond to Behavior Tracking Prompt
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-prompt/{prompt_id}/respond/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "Client showed appropriate requesting behavior when shown cookie. Said 'cookie' clearly and received praise + token."
  }'
```

### Respond to Session Wrap Prompt
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-prompt/{prompt_id}/respond/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "Yes, please generate my session note. I have completed all activities and documented the session data."
  }'
```

**Expected Response:**
```json
{
  "prompt": {
    "id": 456,
    "type": "engagement",
    "message": "How is the session going? Are you hitting your targets today?",
    "response": "Session is going well! Client is engaged and we are hitting our targets.",
    "is_responded": true,
    "responded_at": "2024-01-15T10:35:00Z"
  },
  "message": "Response submitted successfully"
}
```

---

## 🤖 **4. AI Note Generation**

### Generate AI Note
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-ai-note/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "ai_generated_note": "## Session Overview\n\n**Client:** Sophia M.\n**Date:** 2024-01-15\n**Duration:** 10:00 AM - 12:00 PM\n**Staff:** John RBT\n\n## Client Engagement and Behavior Summary\n\nSophia demonstrated excellent engagement throughout the session...\n\n## Detailed Goal Progress\n\n**Requesting Help:** 86% achievement rate with 8/10 successful trials...\n\n## Behavioral Observations (ABC Analysis)\n\n**Antecedent:** Want Cookie? + Showed Cookie\n**Behavior:** Said 'cookie' clearly\n**Consequence:** Praise + Token Given\n\n## Reinforcement Effectiveness\n\nToken economy system was highly effective with 12 applications...\n\n## Recommendations for Next Session\n\n1. Continue with token economy system\n2. Focus on requesting help goal\n3. Maintain current reinforcement schedule",
  "session_data_summary": {
    "activities_count": 3,
    "goals_count": 1,
    "abc_events_count": 1,
    "incidents_count": 0
  },
  "message": "AI note generated successfully"
}
```

---

## ✅ **5. Session Validation and Finalization**

### Check Session End Eligibility
```bash
curl -X GET "{base_url}/api/sessions/{session_id}/ocean-dashboard/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### Finalize Session with Ocean AI Validation
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-finalize/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

**Success Response:**
```json
{
  "can_finalize": true,
  "message": "Session finalized successfully",
  "note_flow_status": {
    "is_note_completed": true,
    "final_note_submitted": true,
    "ai_generated_note": "## Session Overview\n..."
  }
}
```

**Error Response (if note not completed):**
```json
{
  "can_finalize": false,
  "error": "Session note must be completed before finalizing",
  "required_actions": [
    "Complete session note content",
    "Review and finalize session note",
    "Submit final session note"
  ],
  "note_flow_status": {
    "is_note_completed": false,
    "final_note_submitted": false
  }
}
```

---

## 📝 **6. Save Session Data with AI Integration**

### Save Complete Session Data
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/save-and-generate-notes/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "activities": [
      {
        "name": "Discrete Trial Training",
        "duration": 10,
        "description": "Token economy system used",
        "response": "Client appeared motivated and engaged during the session"
      }
    ],
    "goals": [
      {
        "goal": "Requesting help",
        "target": "80% accuracy",
        "trials": 10,
        "successes": 8,
        "percentage": 86,
        "notes": "Good progress with some regression noted"
      }
    ],
    "abc_events": [
      {
        "antecedent": "Want Cookie? + Showed Cookie",
        "behavior": "Said cookie clearly",
        "consequence": "Praise + Token Given"
      }
    ],
    "reinforcement_strategies": [
      {
        "type": "Token economy",
        "effectiveness": 4,
        "description": "Client motivated by token system",
        "notes": "Worked for 90% of session"
      }
    ],
    "incidents": [
      {
        "type": "minor_disruption",
        "severity": "low",
        "duration": 0,
        "description": "No incidents reported"
      }
    ],
    "checklist": {
      "materials_ready": true,
      "environment_prepared": true,
      "reviewed_goals": true,
      "notes": "All pre-session items completed"
    },
    "auto_save": true
  }'
```

**Expected Response:**
```json
{
  "session_id": 123,
  "saved_data": {
    "activities": "1 activities saved",
    "goals": "1 goals saved",
    "abc_events": "1 ABC events saved",
    "reinforcement_strategies": "1 strategies saved",
    "incidents": "1 incidents saved",
    "checklist": "3 checklist items saved"
  },
  "generated_notes": "## Session Overview\n\n**Client:** Sophia M.\n...",
  "auto_saved": true,
  "message": "Session data saved to database and AI notes generated successfully"
}
```

---

## 🔄 **7. Complete Session Flow Testing**

### Step 1: Start Session and Check Dashboard
```bash
curl -X GET "{base_url}/api/sessions/{session_id}/ocean-dashboard/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 2: Create Engagement Prompt
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-prompt/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt_type": "engagement"}'
```

### Step 3: Respond to Prompt
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-prompt/{prompt_id}/respond/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"response": "Session going well, client engaged"}'
```

### Step 4: Save Session Data
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/save-and-generate-notes/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...session_data...}'
```

### Step 5: Create 15-Minute Warning
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-prompt/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt_type": "session_wrap"}'
```

### Step 6: Generate AI Note
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-ai-note/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 7: Finalize Session
```bash
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-finalize/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🧪 **8. Error Testing**

### Test Session End Without Note
```bash
# Try to finalize without completing note
curl -X POST "{base_url}/api/sessions/{session_id}/ocean-finalize/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Invalid Session ID
```bash
curl -X GET "{base_url}/api/sessions/99999/ocean-dashboard/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Unauthorized Access
```bash
# Remove or use invalid token
curl -X GET "{base_url}/api/sessions/{session_id}/ocean-dashboard/"
```

---

## 📋 **9. Postman Collection Setup**

### Environment Variables
Create these variables in Postman:
- `base_url`: `http://localhost:8000`
- `session_id`: `123`
- `prompt_id`: `456`
- `auth_token`: `Bearer YOUR_ACTUAL_TOKEN`

### Headers for All Requests
```
Authorization: {{auth_token}}
Content-Type: application/json
```

### Test Sequence
1. **GET** `/api/sessions/{{session_id}}/ocean-dashboard/`
2. **POST** `/api/sessions/{{session_id}}/ocean-prompt/` (engagement)
3. **POST** `/api/sessions/{{session_id}}/ocean-prompt/{{prompt_id}}/respond/`
4. **POST** `/api/sessions/{{session_id}}/save-and-generate-notes/`
5. **POST** `/api/sessions/{{session_id}}/ocean-prompt/` (session_wrap)
6. **POST** `/api/sessions/{{session_id}}/ocean-ai-note/`
7. **POST** `/api/sessions/{{session_id}}/ocean-finalize/`

---

## ✅ **Testing Checklist**

- [ ] Session dashboard loads with Ocean AI status
- [ ] Engagement prompts can be created and responded to
- [ ] 15-minute warning prompt works correctly
- [ ] AI note generation produces comprehensive notes
- [ ] Session validation prevents ending without notes
- [ ] Complete session flow works end-to-end
- [ ] Error handling works for invalid requests
- [ ] Authentication and permissions work correctly

---

## 🎯 **Expected Results**

After running all tests, you should see:

1. **Active Prompting**: Ocean creates and tracks prompts throughout sessions
2. **Session Validation**: System prevents ending without completed notes
3. **15-Minute Warning**: Automatic wrap-up prompts in final 15 minutes
4. **AI Note Generation**: Professional session notes generated from data
5. **Marketing Features**: Live support demonstration during sessions

The system will keep RBTs engaged, ensure proper documentation, and showcase Ocean's AI capabilities as a live support tool during therapy sessions.
