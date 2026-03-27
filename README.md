# LanguageTeacherproject

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
