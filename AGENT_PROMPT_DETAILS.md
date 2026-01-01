# Agent Prompt & API Call Details

This document shows exactly what prompt we're using and what's being sent to OpenAI.

---

## 📝 The Agent Prompt (Instructions)

**Location**: `apps/api/app/services/agent.py` line 55-99

```
You are a real estate lead qualification assistant.

YOUR GOAL: Qualify leads by collecting complete information to match them with properties.

INFORMATION TO COLLECT:
1. Persona: Are they a buyer, renter, or seller?
2. Location: Which city and specific areas interest them?
3. Property type: Apartment, villa, townhouse, etc.
4. Bedrooms: How many bedrooms do they need?
5. Size: Minimum square meters (optional)
6. Budget: Price range they're comfortable with
7. Timeline: When do they want to move?
8. Financing: Pre-approved? Any financing details?
9. Contact: Verify name, email, phone (for follow-up)
10. Consent: Can we contact them via email/SMS/WhatsApp?

CONVERSATION GUIDELINES:
- Ask ONE question at a time to avoid overwhelming the user
- Be warm, friendly, and conversational
- Use tools to search matching properties when you have enough criteria
- Show relevant matches to build excitement
- If user mentions budget in text (e.g., "around 150k"), use normalize_budget tool
- If user mentions areas, use geo_match to validate
- When you have complete information, use lead_score to calculate quality
- Then call persist_qualification to save the results

EDGE CASES:
- If user provides vague budget ("flexible", "depends"), ask for a range
- If user is unsure about areas, suggest popular ones and use inventory_search
- If user asks about specific property, search and provide details
- If conversation goes off-topic, politely redirect to qualification

WHEN TO FINISH:
- When you have all required information AND have called persist_qualification
- If user asks to stop or speak to a human, acknowledge and end gracefully
- If you cannot help after 3 attempts, suggest human handoff

OUTPUT:
Once you have complete information and have saved it, provide a friendly summary.
```

---

## 📤 What We Send to OpenAI

### API Call Structure

**Endpoint**: `POST https://api.openai.com/v1/chat/completions`

**Headers**:
```json
{
  "Authorization": "Bearer YOUR_OPENAI_API_KEY",
  "Content-Type": "application/json"
}
```

**Request Body**:
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {
      "role": "system",
      "content": "<THE FULL PROMPT ABOVE>"
    },
    {
      "role": "user",
      "content": "hi how are you?"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "inventory_search",
        "description": "Search available properties. Use when user mentions location, type, beds, or budget to show matching options.",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {"type": "string", "description": "City name, e.g., Dubai, Abu Dhabi"},
            "area": {"type": "string", "description": "Specific area/neighborhood"},
            "property_type": {"type": "string", "description": "Type: apartment, villa, townhouse, studio"},
            "beds": {"type": "integer", "description": "Number of bedrooms"},
            "min_price": {"type": "number", "description": "Minimum price in AED"},
            "max_price": {"type": "number", "description": "Maximum price in AED"},
            "min_area_m2": {"type": "integer", "description": "Minimum size in square meters"},
            "limit": {"type": "integer", "description": "Max results to return (default: 5)", "default": 5}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "normalize_budget",
        "description": "Parse budget from natural language text into min/max values. Use when user mentions budget in conversation.",
        "parameters": {
          "type": "object",
          "properties": {
            "text": {"type": "string", "description": "Budget text like '150k', '100-200k', '2 million AED'"}
          },
          "required": ["text"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "geo_match",
        "description": "Validate and normalize geographic area names.",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {"type": "string"},
            "areas": {"type": "array", "items": {"type": "string"}, "description": "List of area names to validate"}
          },
          "required": ["city", "areas"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "lead_score",
        "description": "Calculate lead quality score (0-100). Use when you have collected enough information.",
        "parameters": {
          "type": "object",
          "properties": {
            "profile": {"type": "object", "description": "Lead profile with city, areas, property_type, beds, budget, timeline, etc."},
            "top_matches": {"type": "array", "items": {"type": "object"}, "description": "Top matching units from inventory_search"},
            "contact": {"type": "object", "description": "Contact info with email, phone"}
          },
          "required": ["profile", "top_matches", "contact"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "persist_qualification",
        "description": "Save qualification results to database. Call this LAST after scoring.",
        "parameters": {
          "type": "object",
          "properties": {
            "lead_id": {"type": "integer"},
            "qualified": {"type": "boolean"},
            "score": {"type": "integer"},
            "reasons": {"type": "array", "items": {"type": "string"}},
            "missing_info": {"type": "array", "items": {"type": "string"}},
            "suggested_next_step": {"type": "string"},
            "top_matches": {"type": "array", "items": {"type": "object"}}
          },
          "required": ["lead_id", "qualified", "score", "reasons", "missing_info", "suggested_next_step"]
        }
      }
    }
  ],
  "temperature": 0.7
}
```

---

## 🔄 Conversation Flow (What Happens)

### Turn 1: User says "hi how are you?"

**Step 1: Guardrail Checks**
```
Relevance Check:
  Input: "hi how are you?"
  LLM Call: GPT-4o-mini asks "Is this about real estate?"
  Result: ✓ Relevant (conversational greeting is acceptable)

Safety Check:
  Input: "hi how are you?"
  Moderation API: Check for unsafe content
  Pattern Check: Check for "ignore all", "system:", etc.
  Result: ✓ Safe
```

**Step 2: Main Agent Call**
```
Model: gpt-4o-mini
Messages: [
  {role: "system", content: "<FULL PROMPT>"},
  {role: "user", content: "hi how are you?"}
]
Tools: [5 tools listed above]
Temperature: 0.7
```

**Step 3: Agent Response**
```
OpenAI Returns:
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "Hi there! I'm doing great, thank you! How about you? Are you looking for help with real estate?"
    }
  }]
}
```

**Step 4: Stream to UI**
```
SSE Stream:
data: {"type": "text", "content": "H"}
data: {"type": "text", "content": "i"}
data: {"type": "text", "content": " "}
... (character by character)
data: {"type": "context_update", "context": {...}}
data: [DONE]
```

---

### Turn 2: User says "2BR apartment in Dubai Marina, 150k"

**Step 1: Guardrails** ✓

**Step 2: Main Agent Call**
```
Messages: [
  {role: "system", content: "<FULL PROMPT>"},
  {role: "user", content: "hi how are you?"},
  {role: "assistant", content: "Hi there! I'm doing..."},
  {role: "user", content: "2BR apartment in Dubai Marina, 150k"}
]
```

**Step 3: Agent Decides to Use Tools**
```
OpenAI Returns:
{
  "choices": [{
    "message": {
      "role": "assistant",
      "tool_calls": [
        {
          "id": "call_123",
          "function": {
            "name": "normalize_budget",
            "arguments": '{"text": "150k"}'
          }
        },
        {
          "id": "call_124",
          "function": {
            "name": "inventory_search",
            "arguments": '{"city": "Dubai", "area": "Dubai Marina", "beds": 2, "max_price": 150000}'
          }
        }
      ]
    }
  }]
}
```

**Step 4: We Execute Tools**
```
normalize_budget("150k") → {min: 0, max: 150000, currency: "AED"}
inventory_search({...}) → [
  {unit_id: 1, title: "Spacious 2BR...", price: 150000, ...},
  ...
]
```

**Step 5: Send Tool Results Back**
```
Messages: [
  {role: "system", content: "<PROMPT>"},
  ... previous messages ...
  {role: "assistant", tool_calls: [...]},
  {role: "tool", tool_call_id: "call_123", content: "{min: 0, max: 150000, ...}"},
  {role: "tool", tool_call_id: "call_124", content: "[{unit_id: 1, ...}]"}
]
```

**Step 6: Agent Responds with Results**
```
OpenAI Returns:
{
  "message": {
    "content": "Great! I found a perfect match: Spacious 2BR in Dubai Marina for 150,000 AED..."
  }
}
```

---

## 🐛 Why Duplicate Responses?

Looking at the UI code (lines 115-131), I see we're:
1. ✓ Building the message during streaming (correct)
2. ✗ Adding it again at [DONE] (wrong - this causes duplicate)

**Fixed**: Removed the duplicate addition at [DONE]

---

## 📍 Where to Find the Prompt

**File**: `apps/api/app/services/agent.py`  
**Lines**: 55-99  
**Variable**: `self.instructions`

To modify the prompt:
```bash
# Edit this file
nano apps/api/app/services/agent.py

# Or in your IDE
open apps/api/app/services/agent.py

# Find line 55: self.instructions = """..."""
```

---

## 🔍 How to Debug/Monitor

### See Full Request/Response (Add Logging)

Add this to `apps/api/app/services/agent.py` line 410:

```python
# Before calling OpenAI
logger.info("openai_request", 
    model=self.model,
    messages=messages,
    tool_count=len(self.tools)
)

# After getting response
logger.info("openai_response",
    has_tool_calls=bool(assistant_message.tool_calls),
    content_preview=assistant_message.content[:100] if assistant_message.content else None
)
```

### View API Logs
```bash
tail -f /tmp/api.log | grep -E "(openai|agent|tool)"
```

### Test Directly
```bash
# See exact request
curl -X POST http://localhost:8000/agent/turn \
  -H "Content-Type: application/json" \
  -d '{"message":"2BR in Marina 150k"}' -v
```

---

## 🎛️ Customizing the Agent

### Change the Prompt
Edit `apps/api/app/services/agent.py` line 55:
```python
self.instructions = """Your custom instructions here..."""
```

### Add More Tools
Edit `apps/api/app/services/agent.py` line 101, add to `self.tools` list:
```python
{
    "type": "function",
    "function": {
        "name": "your_tool_name",
        "description": "What it does",
        "parameters": {...}
    }
}
```

Then add execution in `_execute_tool()` method (line 241).

### Adjust Guardrails
- **Relevance**: Line 290 - Edit the classifier prompt
- **Safety**: Line 325 - Add more injection patterns
- **Tool Limits**: Line 35 - Change `max_tool_calls: int = 10`

### Change Model
Line 53:
```python
self.model = "gpt-4o"  # Use smarter model
# or
self.model = "gpt-4o-mini"  # Faster, cheaper (current)
```

---

## 📊 Token Usage per Conversation

**Typical Qualification** (5-7 turns):
```
Turn 1: System prompt (500 tokens) + User (10) + Response (50) = ~560 tokens
Turn 2: + History (100) + Tools (200) + Response (100) = ~400 tokens
Turn 3-5: ~300 tokens each
Final: + Scoring + Save = ~200 tokens

Total: ~2500-3500 tokens per qualification
Cost: ~$0.01-0.02 per lead
```

---

## 🔧 Troubleshooting

### Issue: Duplicate Responses
**Status**: ✅ FIXED (removed duplicate at [DONE])

### Issue: Agent Not Using Tools
**Fix**: Make budget/location more explicit:
- Instead of: "around 150k"
- Try: "budget of 150,000 AED"

### Issue: Tools Failing
**Check**: API logs for tool_execution_failed
```bash
tail -f /tmp/api.log | grep tool_execution_failed
```

---

## 📝 Example: Full Conversation Log

### User Message
```json
{"message": "I need 2BR in Dubai Marina for 150k"}
```

### What's Sent to OpenAI
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "<500-word prompt>"},
    {"role": "user", "content": "I need 2BR in Dubai Marina for 150k"}
  ],
  "tools": [<5 tool definitions>],
  "temperature": 0.7
}
```

### OpenAI Response
```json
{
  "id": "chatcmpl-xxx",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_abc123",
          "function": {
            "name": "inventory_search",
            "arguments": "{\"city\":\"Dubai\",\"area\":\"Dubai Marina\",\"beds\":2,\"max_price\":150000}"
          }
        }
      ]
    }
  }]
}
```

### We Execute Tool
```python
inventory_search(db, {
    "city": "Dubai",
    "area": "Dubai Marina", 
    "beds": 2,
    "max_price": 150000
})

Returns: [
    {
        "unit_id": 1,
        "title": "Spacious 2BR Apartment in Dubai Marina",
        "price": 150000,
        "beds": 2,
        "location": "Dubai Marina, Dubai",
        ...
    }
]
```

### Send Result Back to OpenAI
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "<prompt>"},
    {"role": "user", "content": "I need 2BR in Dubai Marina for 150k"},
    {"role": "assistant", "tool_calls": [...]},
    {"role": "tool", "tool_call_id": "call_abc123", "content": "[{unit_id: 1, ...}]"}
  ],
  "tools": [<5 tools>],
  "temperature": 0.7
}
```

### OpenAI Final Response
```json
{
  "choices": [{
    "message": {
      "content": "Perfect! I found this amazing property: Spacious 2BR Apartment in Dubai Marina for exactly 150,000 AED. It has 120 sqm with sea views. When are you planning to move?"
    }
  }]
}
```

### Stream to UI
```
data: {"type": "tool_start", "tool": "inventory_search"}
data: {"type": "tool_result", "tool": "inventory_search", "result": [...]}
data: {"type": "text", "content": "P"}
data: {"type": "text", "content": "e"}
data: {"type": "text", "content": "r"}
... (each character)
data: {"type": "context_update", "context": {...}}
data: [DONE]
```

---

## 🎯 Summary

**The Prompt**: 500-word detailed instructions in `agent.py` line 55  
**What We Send**: System prompt + conversation history + 5 tool definitions  
**Model**: GPT-4o-mini (fast & cheap)  
**Temperature**: 0.7 (balanced creativity)  
**Tools**: 5 functions (search, budget, geo, score, persist)  
**Guardrails**: 2 LLM checks + 1 moderation API + limits  

**Duplicate Response Issue**: ✅ **FIXED**

---

**Now refresh your chat at http://localhost:5173/chat and try again!**  
The duplicate response should be gone. ✨

