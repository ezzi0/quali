# RAG (Retrieval Augmented Generation) Explained

## ✅ YES - We ARE Using RAG!

**RAG** = Retrieval Augmented Generation

It's a technique where the agent:
1. **Retrieves** relevant information from a knowledge base (Qdrant)
2. **Augments** its response with that retrieved context
3. **Generates** answers using both its training AND the retrieved docs

---

## 🔍 How RAG Works in Your System

### Traditional LLM (No RAG)
```
User: "What is Agency 2.0?"
  ↓
LLM: [Only knows what it was trained on]
  ↓
Response: "I don't have specific information about Agency 2.0..."
```

### With RAG (What We Built) ✅
```
User: "What is Agency 2.0?"
  ↓
Agent: [Calls knowledge_search("What is Agency 2.0?")]
  ↓
Qdrant: [Semantic search across embedded FAQs]
  ↓
Returns: [
  {
    "title": "What is Agency 2.0?",
    "content": "Agency 2.0 is an AI-centered real-estate operating system. AI handles targeting, intake, profiling, affordability previews, matching, and documents. Humans focus on discovery, negotiation, and closing...",
    "relevance_score": 0.95
  }
]
  ↓
Agent: [Includes retrieved content in context]
  ↓
LLM: [Generates answer using retrieved facts]
  ↓
Response: "Agency 2.0 is an AI-centered real-estate operating system where AI handles targeting, intake, profiling, affordability previews, matching, and documents, while humans focus on discovery, negotiation, and closing. The Smart Arm learns from every outcome and updates the system daily."
```

---

## 📦 What's in Your RAG Knowledge Base

**Collection**: `knowledge` in Qdrant  
**Documents**: 10 items (7 FAQs + 3 objection handlers)  
**Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)

### FAQs (7 items)
1. What is Agency 2.0?
2. How is it different from traditional agency?
3. What data is used?
4. Is this a credit check?
5. Will I speak to a person?
6. How is my data protected?
7. What results should we expect?

### Objection Handlers (3 items)
1. "A human does this today"
2. "Bots feel cold"
3. "What if we miss whales?"

---

## 🛠️ The RAG Tool

**Function**: `knowledge_search`  
**Location**: `apps/api/app/services/rag.py`  
**Purpose**: Search FAQs and objections via semantic search

**How It Works**:
```python
# 1. User asks: "Is this a credit check?"
knowledge_search("Is this a credit check?", top_k=3)

# 2. Embed the query (OpenAI)
query_embedding = openai.embeddings.create(
    model="text-embedding-3-small",
    input="Is this a credit check?"
)

# 3. Search Qdrant (cosine similarity)
results = qdrant.search(
    collection="knowledge",
    vector=query_embedding,
    limit=3
)

# 4. Return relevant docs
Returns: [
    {
        "title": "Is this a credit check?",
        "content": "No. We run a friendly affordability preview...",
        "type": "qa",
        "relevance_score": 0.98
    }
]

# 5. Agent uses this to answer
Agent: "No, this is not a credit check. We run a friendly affordability preview to set expectations. We only move to formal verification if you proceed with a property and you consent."
```

---

## 🎯 When Agent Uses RAG

The agent will automatically use `knowledge_search` when:
- User asks "What is Agency 2.0?"
- User asks "Is this a credit check?"
- User asks "Will I speak to a person?"
- User raises objection "I prefer talking to a human"
- User asks about data privacy
- User asks about the process

**It's fully automatic** - the agent decides when to search based on the conversation!

---

## 🔄 RAG vs Regular Tools

| Tool Type | Example | Data Source |
|-----------|---------|-------------|
| **RAG Tool** | knowledge_search | Qdrant (FAQs/objections) |
| **Data Tool** | inventory_search | Postgres (properties) + Qdrant |
| **Function Tool** | normalize_budget | Pure function (no database) |
| **Action Tool** | persist_qualification | Postgres (write) |

---

## 📊 RAG Architecture in Your System

```
┌─────────────────────────────────────────────────────┐
│                   User Question                      │
│         "What is Agency 2.0?"                       │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│                  Agent Reasoning                     │
│   GPT-4o-mini decides: Need to search knowledge     │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│              Tool: knowledge_search                  │
│   1. Embed query (OpenAI Embeddings API)            │
│   2. Search Qdrant (cosine similarity)              │
│   3. Return top 3 matches                           │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│                  Qdrant Vector DB                    │
│  Collection: "knowledge"                            │
│  - 10 embedded FAQ/objection docs                   │
│  - Semantic search (not keyword!)                   │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│              Retrieved Documents                     │
│  [                                                   │
│    {title: "What is Agency 2.0?",                   │
│     content: "Agency 2.0 is an AI-centered...",     │
│     score: 0.95}                                    │
│  ]                                                   │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│          Agent Generates Answer                      │
│   GPT-4o-mini uses retrieved content                │
│   to generate accurate, grounded response           │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│              Stream to User                          │
│   "Agency 2.0 is an AI-centered real-estate         │
│    operating system where AI handles targeting,     │
│    intake, profiling..."                            │
└─────────────────────────────────────────────────────┘
```

---

## 🧠 Two Types of RAG in Your System

### 1. **Knowledge RAG** (FAQs/Objections) ✅ NEW!
- **Collection**: `knowledge`
- **Purpose**: Answer questions about Agency 2.0, process, objections
- **Documents**: 10 curated FAQs
- **Tool**: `knowledge_search`

### 2. **Inventory RAG** (Properties) ✅ EXISTING
- **Collection**: `units`
- **Purpose**: Semantic search over properties
- **Documents**: 8 Dubai properties (will grow)
- **Tool**: `inventory_search` (hybrid: SQL filters + vector search)

---

## 🎓 Example RAG Conversation

**User**: "Is this a credit check? I'm worried about my credit score."

**Behind the Scenes**:
```json
// 1. Agent decides to use knowledge_search
{
  "tool_calls": [{
    "function": {
      "name": "knowledge_search",
      "arguments": "{\"query\": \"Is this a credit check?\"}"
    }
  }]
}

// 2. We execute the tool
knowledge_search("Is this a credit check?", top_k=3)

// 3. Qdrant returns
[
  {
    "title": "Is this a credit check?",
    "content": "No. We run a friendly affordability preview to set expectations. It is not a credit check. We only move to formal verification if you proceed with a property and you consent.",
    "type": "qa",
    "relevance_score": 0.98
  }
]

// 4. Tool result sent back to agent
{
  "role": "tool",
  "content": "[{title: 'Is this a credit check?', content: 'No. We run a friendly affordability preview...', score: 0.98}]"
}

// 5. Agent generates answer using this context
```

**Agent Response**: 
"Not at all! This is not a credit check. We run a friendly affordability preview to set expectations and help you understand your options. We only move to formal verification if you decide to proceed with a specific property and give us your consent. Your credit score is not affected by this conversation."

---

## ✅ Current Status

### Knowledge Base
- ✅ 10 FAQs/objections embedded in Qdrant
- ✅ Collection "knowledge" created
- ✅ Semantic search enabled

### RAG Tool
- ✅ `knowledge_search` function created
- ✅ Added to agent's tool list (now 6 tools total)
- ✅ Agent instructions updated to use it

### Agent Tools (6 Total)
1. ✅ `knowledge_search` - RAG for FAQs/objections (NEW!)
2. ✅ `inventory_search` - Properties search
3. ✅ `normalize_budget` - Budget parsing
4. ✅ `geo_match` - Location validation
5. ✅ `lead_score` - Quality scoring
6. ✅ `persist_qualification` - Save results

---

## 🧪 Test RAG

The agent will auto-reload. Try these questions:

```bash
# Test 1: FAQ
curl -X POST http://localhost:8000/agent/turn \
  -H "Content-Type: application/json" \
  -d '{"message":"What is Agency 2.0?"}'

# Test 2: Objection
curl -X POST http://localhost:8000/agent/turn \
  -H "Content-Type: application/json" \
  -d '{"message":"I prefer talking to a human, bots feel cold"}'

# Test 3: Privacy concern
curl -X POST http://localhost:8000/agent/turn \
  -H "Content-Type: application/json" \
  -d '{"message":"How is my data protected?"}'
```

**Or use the Chat UI**: http://localhost:3000/chat

---

## 📈 Benefits of RAG

### Without RAG
- Agent hallucinates answers
- Inconsistent responses
- Can't answer about Agency 2.0
- No objection handling

### With RAG ✅
- ✅ Grounded in facts (from your knowledge base)
- ✅ Consistent answers (always uses same source)
- ✅ Can answer about Agency 2.0
- ✅ Handles objections professionally
- ✅ Can be updated (just add new docs to Qdrant)

---

## 🔧 Updating Knowledge Base

To add new FAQs:

```python
# Edit: apps/api/app/workers/seed_knowledge.py
FAQ_DATA = [
    ... existing items ...,
    {
        "id": "qa_new_question",
        "title": "New Question?",
        "tags": ["qa"],
        "content": "Answer here..."
    }
]

# Then run:
python -m app.workers.seed_knowledge
```

The agent will immediately have access to the new knowledge!

---

## 🎯 Summary

**Q: Are we using RAG?**  
**A**: ✅ YES! We now have TWO RAG systems:

1. **Knowledge RAG** (NEW!)
   - FAQs about Agency 2.0
   - Objection handlers
   - Process questions

2. **Inventory RAG** (Existing)
   - Property semantic search
   - Match buyer to units

**Both use Qdrant + OpenAI embeddings for semantic search!**

The agent now has:
- ✅ 6 tools (including knowledge_search)
- ✅ 10 FAQs/objections in knowledge base
- ✅ RAG-powered answers
- ✅ Model updated (you set it manually)
- ✅ Duplicate response bug fixed

**Ready to test!** 🚀

