# Vizzy Chat — Conversational Visual AI Backend

A conversational AI backend that lets users generate, refine, and iterate on images through natural language — like ChatGPT, but for visual content creation.

---

## What It Does

Users type what they want in plain language. The system understands, generates, and refines visuals conversationally.

**Examples:**
- "Generate a dramatic oil painting of a sunset" → generates image
- "Make it more golden" → automatically refines the last image
- "Give me 3 versions of this" → generates 3 variants
- "What is Vizzy Chat?" → answers conversationally

---

## Architecture

```
app/
├── api/
│   └── chat.py             # API routes (POST /message, POST /refine)
├── db/
│   ├── database.py         # Database connection (SQLite + SQLAlchemy)
│   └── models.py           # Database tables
├── schemas/
│   └── chat.py             # Request/Response validation (Pydantic)
├── services/
│   ├── orchestrator.py     # AI brain — intent + entity extraction
│   ├── prompt_service.py   # Prompt enhancement via Mistral
│   ├── image_service.py    # Image generation + prompt refinement
│   └── asset_service.py   # Asset CRUD + user style memory
└── main.py                 # FastAPI entry point
```
So sir i have used Mistral api because it's free and available to use as a demo

---

## AI Workflow

```
User Message
     ↓
Step 1: CLASSIFY INTENT
   → image_generation
   → image_refinement
   → general_chat
     ↓
Step 2: EXTRACT ENTITIES
   → subject, style, mood, medium, colors, count
   → is request clear? NO → ask clarification
     ↓
Step 3: ENHANCE PROMPT
   → short message → rich detailed prompt
   → apply user style memory automatically
     ↓
Step 4: GENERATE IMAGE
   → 1 or N image variants
     ↓
Step 5: LEARN & SAVE
   → extract style preferences
   → update user style memory
   → save asset with version tracking
```

---

## Features

### 1. Conversational Image Generation
Users describe what they want in plain language. The system classifies intent, extracts structured entities, enhances the prompt using Mistral AI, and generates the image.

```json
Request:
{
  "conversation_id": 1,
  "message": "Generate a dramatic oil painting of a sunset",
  "count": 1
}

Response:
{
  "intent": "image_generation",
  "count": 1,
  "assets": [{
    "asset_id": 1,
    "image_url": "...",
    "prompt": "A breathtaking sunset over golden mountains, dramatic crimson sky, thick impasto brushstrokes, cinematic lighting, 8K resolution..."
  }],
  "style_learned": {
    "style": "oil painting",
    "mood": "dramatic"
  }
}
```

### 2. Conversational Image Refinement
Users refine images in natural language without providing asset IDs. The system automatically finds the last generated image and refines it intelligently using Mistral AI.

```json
Request:
{
  "conversation_id": 1,
  "message": "Make it more golden"
}

Response:
{
  "intent": "image_refinement",
  "parent_asset_id": 1,
  "assets": [{
    "asset_id": 2,
    "version": 2,
    "prompt": "A golden sunset, warm amber tones, glowing horizon..."
  }]
}
```

### 3. Multi-Image Generation
Users can request multiple variants in a single message.

```json
Request:
{
  "conversation_id": 1,
  "message": "Give me 3 versions of a forest",
  "count": 3
}

Response:
{
  "count": 3,
  "assets": [
    { "asset_id": 3, "image_url": "..." },
    { "asset_id": 4, "image_url": "..." },
    { "asset_id": 5, "image_url": "..." }
  ]
}
```

### 4. Multi-Turn Conversation Memory
Every message is saved and passed as history to Mistral. The system remembers context across the full conversation.

```
Turn 1: "Generate a sunset"     → image created
Turn 2: "Make it dramatic"      → knows which image
Turn 3: "Add mountains"         → knows full history
```

### 5. User Style Memory
After every generation, the system extracts and saves style preferences. These are automatically applied to future requests — users never have to repeat themselves.

```
Request 1: "dramatic oil painting of a sunset"
→ UserStyle saved: { mood: dramatic, medium: oil painting }

Request 2: "generate a forest"
→ Auto-applied: "forest, oil painting style, dramatic mood"
```

### 6. Asset Versioning
Every image is saved as an asset. Refinements create new versions with parent references — giving a full history of every iteration.

```
Asset id=1  version=1  parent=None    ← original
Asset id=2  version=2  parent=1       ← first refinement
Asset id=3  version=3  parent=2       ← second refinement
```

### 7. Smart Clarification
If a request is too vague, the system asks for clarification instead of wasting an API call.

```
User: "paint something"
→ "What would you like me to paint?"

User: "generate 3 dramatic oil paintings of a sunset"
→ generates immediately (request is clear)
```

---

## Database Design

```
Conversation (1)
    │
    ├── Message (many)       ← full chat history
    │     ├── role: "user"
    │     └── role: "assistant"
    │
    ├── Asset (many)         ← generated images
    │     ├── version: 1     ← original
    │     └── version: 2     ← refined (parent_asset_id = v1)
    │
    └── UserStyle (one)      ← learned preferences
          ├── preferred_style
          ├── preferred_mood
          ├── preferred_medium
          └── preferred_colors
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Framework | FastAPI |
| AI Model | Mistral AI (mistral-small-2503) |
| Database | SQLite + SQLAlchemy ORM |
| Validation | Pydantic |
| API Docs | Swagger UI (auto-generated) |
| Environment | python-dotenv |

---

## Setup & Installation

**1. Clone the repository:**
```bash
git clone https://github.com/Pranjal007-AI/vizzy-chat
cd vizzy-chat
```

**2. Create and activate virtual environment:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables:**
```bash
cp .env.example .env
# Add your MISTRAL_API_KEY to .env
```

**5. Run the server:**
```bash
python -m uvicorn app.main:app --reload
```

**6. Open API docs:**
```
http://127.0.0.1:8000/docs
```

---

## API Endpoints

### POST /chat/message
Send a message and get a response based on intent.

**Request:**
```json
{
  "conversation_id": 1,
  "message": "Generate a dramatic sunset",
  "count": 1
}
```

### POST /chat/refine
Manually refine a specific asset by ID.

**Request:**
```json
{
  "asset_id": 1,
  "instruction": "make it more golden",
  "count": 1
}
```

---

## Environment Variables

```env
MISTRAL_API_KEY="mistral_api_key_here"
```

---

## Design Decisions

**Why intent-first routing?**
The system classifies intent before doing anything. This ensures the right pathway is selected and no API calls are wasted.

**Why entity extraction?**
Blindly calling image APIs gives poor results. By extracting subject, style, mood, and medium first, the system understands what the user actually wants before generating.

**Why SQLAlchemy ORM?**
Switching from SQLite (development) to PostgreSQL (production) is a single line change in the connection string.

**Why Mistral AI?**
Fast, cost-effective, and excellent for classification and text tasks. The architecture is model-agnostic — switching to GPT-4 is a one-line change.

---

## Author

Pranjal Parashar