# Complete Session Data Examples for Testing

## 🎯 **Complete Session Data Structure**

Based on the frontend interface and backend code, here's the exact data structure you need:

### **📝 Full Session Data Example**

```json
{
  "activities": [
    {
      "name": "Discrete Trial Training",
      "duration": 10,
      "description": "Token economy system used with picture cards and toys",
      "response": "Client appeared motivated and engaged during the session, with sustained attention on tasks for 25 minutes"
    },
    {
      "name": "Communication Training",
      "duration": 15,
      "description": "Verbal prompts and reinforcement",
      "response": "Client showed good progress with requesting help"
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
    },
    {
      "goal": "Following instructions",
      "target": "90% accuracy",
      "trials": 12,
      "successes": 11,
      "percentage": 92,
      "notes": "Excellent performance today"
    }
  ],
  "abc_events": [
    {
      "antecedent": "Want Cookie? + Showed Cookie",
      "behavior": "Said 'cookie' clearly",
      "consequence": "Praise + Token Given"
    },
    {
      "antecedent": "Asked to clean up toys",
      "behavior": "Cried and threw toy",
      "consequence": "Redirected to task, no token"
    }
  ],
  "reinforcement_strategies": [
    {
      "type": "Token economy",
      "effectiveness": 4,
      "description": "Client motivated by token system",
      "notes": "Worked for 90% of session, very effective"
    },
    {
      "type": "Verbal praise",
      "effectiveness": 5,
      "description": "Immediate verbal reinforcement",
      "notes": "Highly effective for maintaining engagement"
    }
  ],
  "incidents": [
    {
      "type": "minor_disruption",
      "severity": "low",
      "duration": 2,
      "description": "Client cried when asked to clean up, threw one soft block. No injury, moderate intensity (6/10 volume)."
    }
  ],
  "checklist": {
    "materials_ready": true,
    "environment_prepared": true,
    "reviewed_goals": true,
    "notes": "All pre-session items completed successfully"
  },
  "auto_save": true
}
```

---

## 🧪 **Testing Data Examples**

### **1. Minimal Session Data**
```json
{
  "activities": [
    {
      "name": "Basic Training",
      "duration": 5,
      "description": "Simple activity",
      "response": "Client engaged"
    }
  ],
  "goals": [
    {
      "goal": "Basic goal",
      "target": "50% accuracy",
      "trials": 5,
      "successes": 3,
      "percentage": 60,
      "notes": "Some progress made"
    }
  ],
  "abc_events": [
    {
      "antecedent": "Simple request",
      "behavior": "Appropriate response",
      "consequence": "Positive reinforcement"
    }
  ],
  "auto_save": true
}
```

### **2. Complete Session Data (No Incidents)**
```json
{
  "activities": [
    {
      "name": "Discrete Trial Training",
      "duration": 20,
      "description": "Picture cards and token system",
      "response": "Client showed excellent engagement and completed all trials successfully"
    },
    {
      "name": "Communication Practice",
      "duration": 15,
      "description": "Verbal prompts and modeling",
      "response": "Client demonstrated clear requesting behavior"
    },
    {
      "name": "Play-based Learning",
      "duration": 10,
      "description": "Interactive play with educational toys",
      "response": "Client maintained attention and followed instructions well"
    }
  ],
  "goals": [
    {
      "goal": "Requesting help when needed",
      "target": "80% accuracy",
      "trials": 15,
      "successes": 13,
      "percentage": 87,
      "notes": "Strong progress, client is generalizing the skill"
    },
    {
      "goal": "Following 2-step instructions",
      "target": "75% accuracy",
      "trials": 12,
      "successes": 10,
      "percentage": 83,
      "notes": "Good improvement from last session"
    }
  ],
  "abc_events": [
    {
      "antecedent": "Showed cookie and asked 'What do you want?'",
      "behavior": "Said 'cookie' clearly and reached for it",
      "consequence": "Given cookie immediately + verbal praise + token"
    },
    {
      "antecedent": "Asked to put toys away",
      "behavior": "Picked up toys and put in box",
      "consequence": "High five + token + 'Great job!'"
    },
    {
      "antecedent": "Presented difficult task",
      "behavior": "Said 'help please' and looked at therapist",
      "consequence": "Provided assistance + praise for asking"
    }
  ],
  "reinforcement_strategies": [
    {
      "type": "Token economy system",
      "effectiveness": 5,
      "description": "Visual token board with preferred rewards",
      "notes": "Highly effective, client earned 8 tokens total"
    },
    {
      "type": "Verbal praise",
      "effectiveness": 4,
      "description": "Immediate verbal reinforcement for correct responses",
      "notes": "Client responds well to enthusiastic praise"
    },
    {
      "type": "Physical reinforcement",
      "effectiveness": 3,
      "description": "High fives and hugs for major accomplishments",
      "notes": "Used sparingly but very motivating when applied"
    }
  ],
  "incidents": [],
  "checklist": {
    "materials_ready": true,
    "environment_prepared": true,
    "reviewed_goals": true,
    "notes": "Session setup completed without issues"
  },
  "auto_save": true
}
```

### **3. Session with Incidents**
```json
{
  "activities": [
    {
      "name": "Discrete Trial Training",
      "duration": 8,
      "description": "Picture cards with token system",
      "response": "Client was initially engaged but became frustrated after incident"
    }
  ],
  "goals": [
    {
      "goal": "Requesting help",
      "target": "80% accuracy",
      "trials": 5,
      "successes": 2,
      "percentage": 40,
      "notes": "Lower performance due to behavioral incident"
    }
  ],
  "abc_events": [
    {
      "antecedent": "Asked to clean up toys",
      "behavior": "Cried loudly and threw toys",
      "consequence": "Redirected to calm down area, no token given"
    }
  ],
  "reinforcement_strategies": [
    {
      "type": "Token economy",
      "effectiveness": 2,
      "description": "System was less effective due to client distress",
      "notes": "Client lost interest in tokens after incident"
    }
  ],
  "incidents": [
    {
      "type": "minor_disruption",
      "severity": "moderate",
      "duration": 5,
      "description": "Client cried and threw toys when asked to clean up. Crying at volume 7/10, threw 3 items. No injury occurred. Incident lasted 5 minutes before client calmed down."
    }
  ],
  "checklist": {
    "materials_ready": true,
    "environment_prepared": true,
    "reviewed_goals": true,
    "notes": "Pre-session completed, but client was already showing signs of distress"
  },
  "auto_save": true
}
```

---

## 🔧 **cURL Commands with Complete Data**

### **Save Session Data with AI Generation**
```bash
curl -X POST "http://localhost:8000/api/sessions/123/save-and-generate-notes/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "activities": [
      {
        "name": "Discrete Trial Training",
        "duration": 10,
        "description": "Token economy system used with picture cards and toys",
        "response": "Client appeared motivated and engaged during the session, with sustained attention on tasks for 25 minutes"
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
        "notes": "Worked for 90% of session, very effective"
      }
    ],
    "incidents": [
      {
        "type": "minor_disruption",
        "severity": "low",
        "duration": 2,
        "description": "Client cried when asked to clean up, threw one soft block. No injury, moderate intensity (6/10 volume)."
      }
    ],
    "checklist": {
      "materials_ready": true,
      "environment_prepared": true,
      "reviewed_goals": true,
      "notes": "All pre-session items completed successfully"
    },
    "auto_save": true
  }'
```

---

## 📋 **Field Descriptions**

### **Activities Fields:**
- `name`: Activity name (e.g., "Discrete Trial Training")
- `duration`: Duration in minutes
- `description`: What was used (materials, strategies)
- `response`: Client's response and engagement notes

### **Goals Fields:**
- `goal`: Goal description
- `target`: Target percentage
- `trials`: Number of trials attempted
- `successes`: Number of successful trials
- `percentage`: Success percentage
- `notes`: Additional notes about progress

### **ABC Events Fields:**
- `antecedent`: What happened before the behavior
- `behavior`: What the client did
- `consequence`: What happened after the behavior

### **Reinforcement Strategies Fields:**
- `type`: Type of reinforcement used
- `effectiveness`: Rating 1-5
- `description`: How it was implemented
- `notes`: Additional observations

### **Incidents Fields:**
- `type`: Type of incident (minor_disruption, sib, aggression, etc.)
- `severity`: low, moderate, high, critical
- `duration`: Duration in minutes
- `description`: Detailed description of what happened

### **Checklist Fields:**
- `materials_ready`: Boolean
- `environment_prepared`: Boolean
- `reviewed_goals`: Boolean
- `notes`: Additional checklist notes

---

## ✅ **Expected Response**

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
  "generated_notes": "## Session Overview\n\n**Client:** Sophia M.\n**Date:** 2024-01-15\n**Duration:** 10:00 AM - 12:00 PM\n**Staff:** John RBT\n\n## Client Engagement and Behavior Summary\n\nSophia demonstrated excellent engagement throughout the session...",
  "auto_saved": true,
  "message": "Session data saved to database and AI notes generated successfully"
}
```

This is the exact data structure you need to use in your cURL commands for testing the Ocean AI RBT Session Note Flow system!

