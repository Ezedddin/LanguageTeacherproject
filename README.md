# AI Language Tutor — SI405 Project

## Quick start (Anthropic / Claude implementation)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your API key

Create a `.env` file at the project root:

```
ANTHROPIC_API_KEY=your_key_here
```

Optional — override the default model (default: `claude-sonnet-4-6`):

```
CLAUDE_MODEL=claude-sonnet-4-6
```

### 3. Run the Streamlit app

```bash
streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`).

### App flow

1. **Welcome** — choose the language you want to learn, click Start
2. **Assessment** — answer 4 open-ended questions
3. **Processing** — Agent 1 detects your CEFR level (A1–B2), Agent 2 builds your 12-week plan
4. **Lesson** — Agent 3 tutors you with adaptive exercises and structured feedback

---

## Architecture

```
src/
  agents/
    assessment_agent.py   # Agent 1: CEFR detection via Anthropic tool_use
    planning_agent.py     # Agent 2: 12-week plan via LangGraph conditional routing
    tutor_agent.py        # Agent 3: RAG + memory + structured feedback
  graph/
    pipeline.py           # LangGraph pipeline: assessment → planning
app.py                    # Streamlit web UI
requirements.txt
```

---

## Original Gemini-based implementation

The original multi-agent implementation using Google Gemini is still available:

## Agent 1 (tekst): CEFR via Gemini

- Bestand: `assessment_agent.py`
- Verwachte env var: `GEMINI_API_KEY`
- Dependencies: `google-genai`, `pydantic`

Installeer dependencies:

```bash
pip install google-genai pydantic
```

Laad env:

```bash
set -a
source .env
set +a
```

Run:

```bash
python3 assessment_agent.py
```

## Live stemtest (zonder audio op te slaan)

- Bestand: `voice_live_assessment.py`
- Input: microfoon (audio alleen in geheugen)
- Env vars: `OPENAI_API_KEY`, `GEMINI_API_KEY`

Installeer dependencies:

```bash
pip install openai sounddevice numpy google-genai pydantic
```

Run:

```bash
set -a
source .env
set +a
python3 voice_live_assessment.py
```

## Bot 3: Tutor agent (LangGraph + RAG + memory)

- Bestand: `tutor-agent/tutor_agent.py`
- Knowledge base: `tutor-agent/knowledge_base.json`
- Session memory opslag: `tutor-agent/session_memory.json` (automatisch aangemaakt)
- Input verwacht van:
  - Bot 1: `AssessmentResult`
  - Bot 2: `LearningPlan`

Dependencies:

```bash
pip install google-genai pydantic langgraph
```

Run demo:

```bash
set -a
source .env
set +a
python3 tutor-agent/tutor_agent.py
```

## Volledige pipeline (Bot 1 -> Bot 2 -> Bot 3)

- Bestand: `run_pipeline.py`
- Draait assessment, planning en tutor in 1 command.

Run:

```bash
set -a
source .env
set +a
python3 run_pipeline.py \
  --answer1 "Hello, my name is Sofia." \
  --answer2 "I am from Spain and now I live in Berlin." \
  --answer3 "I like reading and playing volleyball." \
  --answer4 "Today I worked and then cooked dinner." \
  --user-input "Can we practice my past tense?"
```

Optioneel alleen 1 JSON object:

```bash
python3 run_pipeline.py \
  --answer1 "..." --answer2 "..." --answer3 "..." --answer4 "..." \
  --user-input "..." \
  --json-only
```

## Webapp (Vue + FastAPI)

### Backend starten

```bash
cd webapp/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend heeft ook een aanroepbare TTS tool endpoint:
- `POST /api/tools/tts`
- gebruikt een echte LangChain tool (`@tool`) met `pyttsx3`
- maakt geen audiobestand; spreekt direct op de machine waar de backend draait

### Frontend starten

```bash
cd webapp/frontend
npm install
npm run dev
```

Open daarna de URL uit Vite (meestal `http://localhost:5173`).
In de app staat de API base standaard op `http://localhost:8000`.

De UX-flow is nu:
1. Welkomsscherm met **Start**
2. Vraag 1
3. Vraag 2
4. Vraag 3
5. Vraag 4
6. Automatisch verwerken via Bot 1 -> Bot 2 -> Bot 3 en resultaat tonen
