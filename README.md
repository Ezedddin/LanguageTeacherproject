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
