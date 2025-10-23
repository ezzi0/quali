# Session Persistence & Conversation Recovery

## ✅ Issues Fixed

### Issue 1: Agent Stops Responding After Tool Calls
**Problem**: Agent would call tools (e.g., `geo_match` for "Palm Jumeirah") but not respond with text

**Root Cause**: After executing tools, the agent needs to make **another** API call to GPT-5 to get its text response using the tool results. The original code only called once.

**Fix**: Implemented multi-round tool call loop (up to 3 rounds):
```python
# After tools execute:
for round in range(3):
    # Call GPT-5 again with tool results
    response = openai.chat.completions.create(...)
    
    if response.has_more_tools():
        # Execute those tools too
        continue
    
    if response.has_text():
        # Got the answer! Stream it
        break
```

**Location**: `apps/api/app/services/agent.py` lines 518-601

**Result**: ✅ Agent now responds properly after calling tools!

---

### Issue 2: Session Persistence for Returning Users
**Problem**: User leaves site and comes back → loses conversation history

**Solution**: Implemented Redis-backed session storage with multiple recovery methods

---

## 🔄 How Session Recovery Works

### Step 1: User Visits Chat
```
User opens http://localhost:3000/chat
  ↓
UI checks localStorage:
  - quali_session_id
  - quali_email (if previously captured)
  - quali_phone (if previously captured)
```

### Step 2: Try to Recover Session
```
POST /agent/session
Body: {
  email: "user@example.com",  // if stored
  phone: "+971501234567"      // if stored
}

Backend checks Redis:
1. session:email:user@example.com → session_id
2. session:phone:+971501234567 → session_id
3. session:{session_id} → full conversation context

If found:
  → Returns full conversation history ✓
  → UI displays all previous messages ✓
```

### Step 3: Continue Conversation
```
User can continue exactly where they left off, even days later!
```

---

## 💾 What Gets Stored

### In Redis (7-day TTL)
```json
Key: "session:{uuid}"
Value: {
  "lead_id": 123,
  "session_id": "abc-123-def",
  "conversation_history": [
    {"role": "user", "content": "I want a 2BR in Marina"},
    {"role": "assistant", "content": "Great! What's your budget?"},
    ...
  ],
  "collected_data": {
    "persona": "buyer",
    "city": "Dubai",
    "areas": ["Dubai Marina"],
    "beds": 2,
    "email": "user@example.com",  // Auto-detected!
    "phone": "+971501234567"       // Auto-detected!
  },
  "tool_call_count": 5
}
```

### In Browser localStorage
```javascript
{
  "quali_session_id": "abc-123-def",
  "quali_email": "user@example.com",  // If captured
  "quali_phone": "+971501234567"      // If captured
}
```

---

## 📧 Email/Phone Auto-Capture

The system **automatically detects** email and phone from conversation!

### Example Conversation
```
Agent: "What's your budget for the property?"
User: "Around 2 million AED. My email is john@example.com"

→ System detects: john@example.com
→ Stores in Redis: session:email:john@example.com
→ Stores in localStorage: quali_email
→ Next visit: User can resume by email!
```

### Detection Method
```python
# apps/api/app/services/session_store.py

# Scans conversation for patterns:
email_pattern = r'\b[\w\.-]+@[\w\.-]+\.\w+\b'
phone_pattern = r'\+?\d{10,15}'

# Also checks collected_data field
if context.collected_data.get("email"):
    index_by_email()
```

---

## 🔄 Recovery Flow Diagram

```
User Returns to Site
    ↓
Check localStorage
    ├─ Has session_id? → Load from Redis
    ├─ Has email? → Find session by email
    └─ Has phone? → Find session by phone
    ↓
Session Found?
    ├─ YES → Load full conversation history
    │         Display all previous messages
    │         User continues where they left off
    │
    └─ NO  → Create new session
              Fresh conversation
```

---

## 🎯 Use Cases Covered

### 1. Same Device, Same Browser
- Session ID in localStorage
- **Auto-resumes** on return ✅

### 2. Different Device, Has Email
- User previously mentioned: "My email is sarah@example.com"
- Next time visits chat, provides email
- **Recovers** full conversation ✅

### 3. Different Device, Has Phone
- User previously mentioned: "+971501234567"
- Returns, provides phone
- **Recovers** full conversation ✅

### 4. Anonymous User Returns (Within 7 Days)
- Browser localStorage has session_id
- **Auto-resumes** ✅

### 5. After 7 Days
- Redis TTL expires
- Fresh session created
- (Can extend TTL if needed)

---

## 🛠️ API Endpoints

### Create/Resume Session
```bash
POST /agent/session
{
  "email": "user@example.com",  // optional
  "phone": "+971501234567",     // optional
  "lead_id": 123                // optional
}

Response:
{
  "session_id": "abc-123",
  "context": {...},
  "resumed": true  // or false if new
}
```

### Agent Turn (Auto-Saves)
```bash
POST /agent/turn
{
  "message": "I want a 2BR apartment",
  "session_id": "abc-123",
  "context": {...}  // optional
}

# Automatically:
# - Saves context to Redis after each turn
# - Indexes by email if detected
# - Indexes by phone if detected
```

---

## 📱 Frontend Implementation

**Location**: `apps/web/app/chat/page.tsx`

### On Page Load
```typescript
useEffect(() => {
  initializeSession()  // Checks localStorage, tries to recover
}, [])
```

### Auto-Capture Email/Phone
```typescript
// When context updates with email/phone
if (event.type === 'context_update') {
  if (event.context?.collected_data?.email) {
    localStorage.setItem('quali_email', email)
  }
  if (event.context?.collected_data?.phone) {
    localStorage.setItem('quali_phone', phone)
  }
}
```

### On User Return
```typescript
// Session ID in localStorage → Resume automatically
// or email/phone → API finds session → Resume
```

---

## 🧪 Testing Session Persistence

### Test 1: Same Browser Return
```bash
# 1. Start conversation
Visit: http://localhost:3000/chat
Say: "I want a 2BR apartment"
Agent: "Great! What's your budget?"

# 2. Close tab/browser

# 3. Return to http://localhost:3000/chat
Result: ✅ Conversation history restored!
```

### Test 2: Email Recovery
```bash
# 1. In chat, mention your email
Say: "My email is test@example.com and I want a property"

# 2. Clear localStorage or open incognito

# 3. Visit chat, when agent asks for contact info
Say: "test@example.com"

Result: ✅ Previous conversation recovered!
```

### Test 3: Phone Recovery
```bash
# Same as above but with phone number
Say: "+971501234567"

Result: ✅ Conversation recovered by phone!
```

---

## ⚙️ Configuration

### Redis TTL (Session Expiry)
**Current**: 7 days  
**Location**: `apps/api/app/services/session_store.py` line 31

```python
self.ttl = 86400 * 7  # 7 days

# To change:
self.ttl = 86400 * 30  # 30 days
```

### Storage Keys
```python
# Session by ID
"session:{uuid}"

# Session by email
"session:email:{email_lowercase}"

# Session by phone
"session:phone:{normalized_phone}"
```

---

## 🎯 Summary of Fixes

| Issue | Status | Solution |
|-------|--------|----------|
| Agent stops after tool calls | ✅ Fixed | Multi-round tool call loop |
| Duplicate responses | ✅ Fixed | Removed duplicate in UI |
| Lost sessions on return | ✅ Fixed | Redis persistence |
| Email recovery | ✅ Implemented | Auto-detect + index |
| Phone recovery | ✅ Implemented | Auto-detect + index |
| localStorage persistence | ✅ Implemented | Browser-based resume |

---

## 🚀 Now Test It!

### Full Conversation Test
```
1. Visit: http://localhost:3000/chat
2. Say: "Hi, I want a property in Palm Jumeirah"
3. Agent: Should now respond with text after calling tools ✓
4. Continue conversation...
5. Mention: "My email is test@example.com"
6. Close browser
7. Reopen: http://localhost:3000/chat
8. Result: Conversation restored! ✓
```

**Both issues fixed and session persistence added!** 🎊

