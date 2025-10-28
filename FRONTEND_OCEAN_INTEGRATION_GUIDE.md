# Frontend Ocean AI Integration Guide

## Overview
This guide shows how to integrate the existing RBT session frontend with the Ocean AI backend to create a complete RBT Session Note Flow system.

## 🎯 Frontend-Backend Integration Map

### **Existing Frontend Elements → New Backend Endpoints**

| Frontend Element | Backend Endpoint | Purpose |
|------------------|------------------|---------|
| **Timer (00:00:00)** | `GET /api/sessions/{id}/ocean-dashboard/` | Get session timing and Ocean status |
| **Activities Table** | `POST /api/sessions/{id}/save-and-generate-notes/` | Save activities + trigger AI prompts |
| **ABC Events Table** | `POST /api/sessions/{id}/save-and-generate-notes/` | Save ABC data + trigger AI prompts |
| **Goals Progress** | `POST /api/sessions/{id}/save-and-generate-notes/` | Save goals + trigger AI prompts |
| **Save & Add Note** | `POST /api/sessions/{id}/ocean-finalize/` | Validate and finalize with Ocean AI |
| **Preview Button** | `POST /api/sessions/{id}/ocean-ai-note/` | Generate AI note preview |

## 🔧 Required Frontend Enhancements

### 1. **Add Ocean AI Prompt Interface**

Add this to your frontend session page:

```javascript
// Ocean AI Prompt Component
const OceanPromptNotification = ({ sessionId }) => {
  const [currentPrompt, setCurrentPrompt] = useState(null);
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Check for active prompts
  useEffect(() => {
    const checkPrompts = async () => {
      try {
        const response = await fetch(`/api/sessions/${sessionId}/ocean-dashboard/`);
        const data = await response.json();
        
        // Find pending prompts
        const pendingPrompts = data.ocean_integration.prompts.list.filter(p => !p.is_responded);
        if (pendingPrompts.length > 0) {
          setCurrentPrompt(pendingPrompts[0]);
        }
      } catch (error) {
        console.error('Error checking prompts:', error);
      }
    };

    checkPrompts();
    const interval = setInterval(checkPrompts, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [sessionId]);

  const handleRespond = async () => {
    if (!currentPrompt || !response.trim()) return;

    setIsLoading(true);
    try {
      const response = await fetch(`/api/sessions/${sessionId}/ocean-prompt/${currentPrompt.id}/respond/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ response: response })
      });

      if (response.ok) {
        setCurrentPrompt(null);
        setResponse('');
        // Refresh dashboard
        window.location.reload();
      }
    } catch (error) {
      console.error('Error responding to prompt:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!currentPrompt) return null;

  return (
    <div className="ocean-prompt-notification" style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      background: '#1a1a1a',
      border: '2px solid #4CAF50',
      borderRadius: '8px',
      padding: '20px',
      maxWidth: '400px',
      zIndex: 1000
    }}>
      <h4 style={{ color: '#4CAF50', margin: '0 0 10px 0' }}>🤖 Ocean Assistant</h4>
      <p style={{ color: 'white', margin: '0 0 15px 0' }}>{currentPrompt.message}</p>
      <textarea
        value={response}
        onChange={(e) => setResponse(e.target.value)}
        placeholder="Your response..."
        style={{
          width: '100%',
          height: '80px',
          background: '#333',
          color: 'white',
          border: '1px solid #555',
          borderRadius: '4px',
          padding: '8px',
          marginBottom: '10px'
        }}
      />
      <button
        onClick={handleRespond}
        disabled={isLoading || !response.trim()}
        style={{
          background: '#4CAF50',
          color: 'white',
          border: 'none',
          padding: '8px 16px',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        {isLoading ? 'Submitting...' : 'Submit Response'}
      </button>
    </div>
  );
};
```

### 2. **Add 15-Minute Warning Display**

```javascript
// 15-Minute Warning Component
const SessionWarning = ({ sessionId }) => {
  const [warningData, setWarningData] = useState(null);

  useEffect(() => {
    const checkWarning = async () => {
      try {
        const response = await fetch(`/api/sessions/${sessionId}/ocean-dashboard/`);
        const data = await response.json();
        
        if (data.session.in_final_15_minutes) {
          setWarningData({
            timeRemaining: data.session.time_remaining_minutes,
            message: "Session ending soon - consider wrapping up activities"
          });
        }
      } catch (error) {
        console.error('Error checking warning:', error);
      }
    };

    checkWarning();
    const interval = setInterval(checkWarning, 60000); // Check every minute
    return () => clearInterval(interval);
  }, [sessionId]);

  if (!warningData) return null;

  return (
    <div className="session-warning" style={{
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      background: '#ff6b35',
      color: 'white',
      padding: '20px',
      borderRadius: '8px',
      textAlign: 'center',
      zIndex: 1001,
      boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
    }}>
      <h3>⏰ Session Ending Soon</h3>
      <p>{warningData.message}</p>
      <p>Time remaining: {warningData.timeRemaining} minutes</p>
      <button
        onClick={() => generateAINote(sessionId)}
        style={{
          background: 'white',
          color: '#ff6b35',
          border: 'none',
          padding: '10px 20px',
          borderRadius: '4px',
          cursor: 'pointer',
          marginTop: '10px'
        }}
      >
        Generate AI Note
      </button>
    </div>
  );
};
```

### 3. **Add AI Note Generation Section**

```javascript
// AI Note Generation Component
const AINoteSection = ({ sessionId }) => {
  const [aiNote, setAiNote] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const generateAINote = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch(`/api/sessions/${sessionId}/ocean-ai-note/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const data = await response.json();
        setAiNote(data.ai_generated_note);
      }
    } catch (error) {
      console.error('Error generating AI note:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="ai-note-section" style={{
      background: '#2a2a2a',
      border: '1px solid #444',
      borderRadius: '8px',
      padding: '20px',
      margin: '20px 0'
    }}>
      <h3 style={{ color: '#4CAF50', margin: '0 0 15px 0' }}>🤖 AI Note Generation</h3>
      
      <button
        onClick={generateAINote}
        disabled={isGenerating}
        style={{
          background: '#4CAF50',
          color: 'white',
          border: 'none',
          padding: '10px 20px',
          borderRadius: '4px',
          cursor: 'pointer',
          marginBottom: '15px'
        }}
      >
        {isGenerating ? 'Generating...' : 'Generate AI Note'}
      </button>

      {aiNote && (
        <div style={{
          background: '#1a1a1a',
          border: '1px solid #555',
          borderRadius: '4px',
          padding: '15px',
          marginTop: '15px'
        }}>
          <h4 style={{ color: 'white', margin: '0 0 10px 0' }}>Generated Note Preview:</h4>
          <div style={{
            color: '#ccc',
            whiteSpace: 'pre-wrap',
            maxHeight: '300px',
            overflowY: 'auto'
          }}>
            {aiNote}
          </div>
        </div>
      )}
    </div>
  );
};
```

### 4. **Add Session Validation Feedback**

```javascript
// Session Validation Component
const SessionValidation = ({ sessionId }) => {
  const [validationData, setValidationData] = useState(null);

  useEffect(() => {
    const checkValidation = async () => {
      try {
        const response = await fetch(`/api/sessions/${sessionId}/ocean-dashboard/`);
        const data = await response.json();
        setValidationData(data.ocean_integration);
      } catch (error) {
        console.error('Error checking validation:', error);
      }
    };

    checkValidation();
    const interval = setInterval(checkValidation, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, [sessionId]);

  if (!validationData || validationData.can_end_session) return null;

  return (
    <div className="session-validation" style={{
      background: '#ff4444',
      color: 'white',
      padding: '15px',
      borderRadius: '8px',
      margin: '20px 0',
      border: '2px solid #ff6666'
    }}>
      <h4>⚠️ Session Cannot Be Ended</h4>
      <p>Session note must be completed before ending session</p>
      <ul style={{ margin: '10px 0', paddingLeft: '20px' }}>
        {validationData.blocking_reasons.map((reason, index) => (
          <li key={index}>{reason}</li>
        ))}
      </ul>
      <div style={{ marginTop: '10px' }}>
        <strong>Required Actions:</strong>
        <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
          {validationData.recommendations.map((rec, index) => (
            <li key={index}>{rec}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};
```

### 5. **Enhanced Save & Add Note Button**

```javascript
// Enhanced Save Button with Ocean AI Integration
const EnhancedSaveButton = ({ sessionId, sessionData }) => {
  const [isSaving, setIsSaving] = useState(false);
  const [validationError, setValidationError] = useState(null);

  const handleSaveWithOcean = async () => {
    setIsSaving(true);
    setValidationError(null);

    try {
      // First, save session data
      const saveResponse = await fetch(`/api/sessions/${sessionId}/save-and-generate-notes/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sessionData)
      });

      if (!saveResponse.ok) {
        throw new Error('Failed to save session data');
      }

      // Then, try to finalize with Ocean AI validation
      const finalizeResponse = await fetch(`/api/sessions/${sessionId}/ocean-finalize/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (finalizeResponse.ok) {
        const data = await finalizeResponse.json();
        alert('Session finalized successfully!');
        // Redirect or update UI
      } else {
        const errorData = await finalizeResponse.json();
        setValidationError(errorData);
      }
    } catch (error) {
      console.error('Error saving session:', error);
      alert('Error saving session: ' + error.message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <button
        onClick={handleSaveWithOcean}
        disabled={isSaving}
        style={{
          background: isSaving ? '#666' : '#ff6b35',
          color: 'white',
          border: 'none',
          padding: '12px 24px',
          borderRadius: '4px',
          cursor: isSaving ? 'not-allowed' : 'pointer',
          fontSize: '16px'
        }}
      >
        {isSaving ? 'Saving...' : 'Save & Add Note'}
      </button>

      {validationError && (
        <div style={{
          background: '#ff4444',
          color: 'white',
          padding: '10px',
          borderRadius: '4px',
          marginTop: '10px'
        }}>
          <strong>Cannot save session:</strong>
          <p>{validationError.error}</p>
          <ul>
            {validationError.required_actions?.map((action, index) => (
              <li key={index}>{action}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
```

## 🔄 Complete Integration Flow

### **1. Session Start**
```javascript
// Initialize Ocean AI integration
useEffect(() => {
  const initializeOcean = async () => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}/ocean-dashboard/`);
      const data = await response.json();
      
      // Check if in final 15 minutes
      if (data.session.in_final_15_minutes) {
        // Show 15-minute warning
        setShowWarning(true);
      }
      
      // Check for pending prompts
      if (data.ocean_integration.prompts.pending > 0) {
        // Show prompt notification
        setShowPrompt(true);
      }
    } catch (error) {
      console.error('Error initializing Ocean:', error);
    }
  };

  initializeOcean();
}, [sessionId]);
```

### **2. During Session - Active Prompting**
```javascript
// Check for prompts every 30 seconds
useEffect(() => {
  const checkPrompts = setInterval(async () => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}/ocean-dashboard/`);
      const data = await response.json();
      
      // Show new prompts
      if (data.ocean_integration.prompts.pending > 0) {
        setCurrentPrompt(data.ocean_integration.prompts.list[0]);
      }
    } catch (error) {
      console.error('Error checking prompts:', error);
    }
  }, 30000);

  return () => clearInterval(checkPrompts);
}, [sessionId]);
```

### **3. Final 15 Minutes - Wrap-up Prompt**
```javascript
// Check for 15-minute warning
useEffect(() => {
  const checkWarning = setInterval(async () => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}/ocean-dashboard/`);
      const data = await response.json();
      
      if (data.session.in_final_15_minutes) {
        setShowWarning(true);
        // Auto-create wrap-up prompt
        await fetch(`/api/sessions/${sessionId}/ocean-prompt/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt_type: 'session_wrap' })
        });
      }
    } catch (error) {
      console.error('Error checking warning:', error);
    }
  }, 60000);

  return () => clearInterval(checkWarning);
}, [sessionId]);
```

### **4. Session End Validation**
```javascript
// Validate before ending session
const handleEndSession = async () => {
  try {
    const response = await fetch(`/api/sessions/${sessionId}/ocean-finalize/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    if (response.ok) {
      // Session can be ended
      alert('Session ended successfully!');
    } else {
      const errorData = await response.json();
      // Show validation error
      setValidationError(errorData);
    }
  } catch (error) {
    console.error('Error ending session:', error);
  }
};
```

## 📊 API Endpoints Summary

| Endpoint | Method | Purpose | Frontend Usage |
|----------|--------|---------|----------------|
| `/api/sessions/{id}/ocean-dashboard/` | GET | Get session status with Ocean AI | Load session dashboard |
| `/api/sessions/{id}/ocean-prompt/` | POST | Create Ocean prompt | Trigger engagement prompts |
| `/api/sessions/{id}/ocean-prompt/{prompt_id}/respond/` | POST | Respond to prompt | RBT responds to prompts |
| `/api/sessions/{id}/ocean-ai-note/` | POST | Generate AI note | Preview button functionality |
| `/api/sessions/{id}/ocean-finalize/` | POST | Finalize with validation | Save & Add Note button |

## ✅ Implementation Checklist

- [ ] Add Ocean AI prompt notification component
- [ ] Add 15-minute warning display
- [ ] Add AI note generation section
- [ ] Add session validation feedback
- [ ] Enhance Save & Add Note button with validation
- [ ] Add real-time prompt checking (every 30 seconds)
- [ ] Add 15-minute warning checking (every minute)
- [ ] Add session end validation
- [ ] Test all Ocean AI integrations
- [ ] Add error handling for all Ocean AI calls

## 🎯 Result

With these enhancements, your frontend will have:

1. **Active Prompting**: Ocean prompts RBTs throughout sessions
2. **Session Validation**: Prevents ending without completed notes
3. **15-Minute Warning**: Automatic wrap-up prompts
4. **AI Note Generation**: Professional note creation
5. **Marketing Features**: Live support demonstration

The frontend will now be fully integrated with the Ocean AI backend, creating a complete RBT Session Note Flow system that keeps therapists engaged and ensures proper documentation.
