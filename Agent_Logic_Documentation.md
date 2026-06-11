# Smart GDD Creator — Agent Logic Documentation

**Project:** Smart GDD Creator  
**Version:** 2.0  
**Stack:** Gemini Flash · Claude Sonnet · Claude Haiku · Streamlit · Python

---

## 1. System Overview

The Smart GDD Creator is a multi-agent AI system that transforms a single-sentence game idea into a complete, studio-grade Game Design Document (GDD). It orchestrates four specialized agents in sequence, each building on the previous agent's output through a shared state dictionary.

```
User Input → Planner → Researcher → Writer → Reviewer → Final GDD
                                        ↑          |
                                        └──────────┘
                                      (revision loop, max 1)
```

---

## 2. Core Call Function

Every agent is powered by a single shared function — `call_model()` — defined in `utils/router.py`. This is the engine the entire system runs on.

```python
def call_model(agent_name, system_prompt, user_message):
    config = AGENT_MAP[agent_name]
    try:
        if config['provider'] == 'gemini':
            return _call_gemini(config['model'], system_prompt, user_message)
        else:
            return _call_anthropic(config['model'], system_prompt, user_message)
    except Exception as e:
        # automatic fallback to the other provider
        ...
```

**Why one function?** It enforces a single contract across all agents — any change to retry logic, logging, or model switching happens in one place.

---

## 3. Multi-Provider Routing

Agents are matched to the model best suited for their task:

| Agent | Provider | Model | Reason |
|---|---|---|---|
| Planner | Gemini Flash | gemini-1.5-flash-latest | Fast structured JSON, free tier |
| Researcher | Gemini Flash | gemini-1.5-flash-latest | Factual, fast, free tier |
| Writer | Claude Sonnet | claude-sonnet-4-5 | Best creative long-form writing |
| Reviewer | Claude Haiku | claude-haiku-4-5-20251001 | Analytical scoring, cheapest |

The routing table `AGENT_MAP` in `router.py` is the single place to swap any model — no agent code needs to change.

---

## 4. Agent Logic

### 4.1 Planner Agent
**File:** `agents/planner.py`  
**Provider:** Gemini Flash

**Input:** Raw one-line game idea  
**Output:** Structured JSON with 7 design pillars

**What it does:** Expands a vague idea into a concrete design framework. It defines the genre, the core gameplay loop, the target audience, the platform, the tone, three design pillars, and the unique hook that differentiates the game.

**Why Gemini Flash:** The task is purely structural — extract and organize. No creative depth needed. Flash handles it in under 3 seconds.

```python
def run_planner(idea: str) -> dict:
    raw = call_model_with_fallback("planner", SYSTEM_PROMPT, f"Game idea: {idea}")
    return json.loads(raw)
```

---

### 4.2 Researcher Agent
**File:** `agents/researcher.py`  
**Provider:** Gemini Flash

**Input:** Idea + Planner output  
**Output:** Market analysis JSON

**What it does:** Grounds the design in market reality. Finds 2-3 comparable games with revenue data, identifies the market gap the game can fill, flags the main commercial risk, and estimates audience size.

**Why it matters:** Without this step, the Writer could produce a GDD for a game that's already been done — or that targets a non-existent market.

```python
def run_researcher(idea: str, planner: dict) -> dict:
    msg = f"Idea: {idea}\nPillars: {json.dumps(planner)}"
    raw = call_model_with_fallback("researcher", SYSTEM_PROMPT, msg)
    return json.loads(raw)
```

---

### 4.3 Writer Agent ⭐ Most Important
**File:** `agents/writer.py`  
**Provider:** Claude Sonnet

**Input:** Idea + Planner output + Researcher output  
**Output:** Full 9-section GDD JSON

**What it does:** Generates the complete Game Design Document. It reads everything both upstream agents produced and writes nine sections: story, protagonist, core mechanic, progression system, level design, UI/UX notes, monetization, art direction, and free asset recommendations.

**Why Claude Sonnet:** Creative writing quality matters most here. Claude produces significantly richer narrative premises, more specific protagonist backstories, and more coherent art direction descriptions than flash models. This is the section users will actually read and judge.

**Optimization applied:** The system prompt caps each field at 2-4 sentences. This keeps the response fast while still producing high-quality output — and eliminates token truncation issues that caused `JSONDecodeError`.

```python
def run_writer(idea: str, planner: dict, researcher: dict) -> dict:
    msg = (
        f"Game idea: {idea}\n\n"
        f"Design pillars: {json.dumps(planner, indent=2)}\n\n"
        f"Market research: {json.dumps(researcher, indent=2)}"
    )
    raw = call_model_with_fallback("writer", SYSTEM_PROMPT, msg)
    return json.loads(raw)
```

---

### 4.4 Reviewer Agent
**File:** `agents/reviewer.py`  
**Provider:** Claude Haiku

**Input:** All three upstream outputs  
**Output:** Score, pass/fail, strengths, issues, recommendation

**What it does:** Acts as a quality gate. Evaluates the GDD for feasibility, completeness, and internal coherence. Returns a score from 1-10. If `passed=false` (score < 7), it triggers a revision loop that sends the pipeline back to the Writer.

**Why Claude Haiku:** Analytical scoring doesn't need creative depth — it needs precision and speed. Haiku is the cheapest Claude model and fastest for structured evaluation tasks.

```python
def run_reviewer(planner: dict, researcher: dict, writer: dict) -> dict:
    msg = (
        f"Planner output: {json.dumps(planner)}\n"
        f"Researcher output: {json.dumps(researcher)}\n"
        f"Writer output: {json.dumps(writer)}"
    )
    raw = call_model_with_fallback("reviewer", SYSTEM_PROMPT, msg)
    return json.loads(raw)
```

---

## 5. Pipeline Orchestrator

**File:** `app/pipeline.py`

The pipeline runs all four agents in sequence and manages the revision loop. It is the only file that knows the full execution order — agents themselves don't reference each other.

```python
def run_pipeline(idea: str):
    # Sequential execution
    state['planner_output']    = run_planner(idea)
    state['researcher_output'] = run_researcher(idea, planner_output)

    # Revision loop
    while revision_count <= MAX_REVISIONS:
        state['writer_output']   = run_writer(idea, planner_output, researcher_output)
        state['reviewer_output'] = run_reviewer(planner_output, researcher_output, writer_output)

        if reviewer_output['passed']:
            break               # ✅ GDD passed
        revision_count += 1     # 🔄 retry
```

**MAX_REVISIONS = 1** — one retry is enough for a demo. In production this could be 2-3 with increasingly specific feedback injected into the Writer's context.

---

## 6. JSON Safety — `_extract_json()`

Every model call is parsed through `_extract_json()` before `json.loads()`. This eliminates `JSONDecodeError` regardless of what any model returns.

```python
def _extract_json(text: str) -> str:
    # Strip markdown fences
    text = re.sub(r'```(?:json)?', '', text).strip().rstrip('`').strip()
    # Find the outermost JSON object
    start = text.find('{')
    end   = text.rfind('}')
    return text[start:end+1]
```

This handles: markdown-wrapped responses, preamble text before JSON, trailing commentary after JSON, and partial responses from flash models.

---

## 7. Shared State & Memory

Agents communicate exclusively through a shared `state` dictionary — they never call each other directly.

```
state = {
  'idea':               "...",        # user input
  'planner_output':     {...},        # set by Planner
  'researcher_output':  {...},        # set by Researcher
  'writer_output':      {...},        # set by Writer
  'reviewer_output':    {...},        # set by Reviewer
  'review_passed':      True/False,
  'revision_count':     0,
}
```

In the Streamlit app, this state lives in `st.session_state` so it persists across UI interactions without re-running the full pipeline.

---

## 8. Automatic Fallback

If either provider fails (quota exhausted, network error, deprecated model), the router automatically switches to the other provider:

```
Primary fails → fallback fires → demo continues without crashing
```

This is what the `⚠️ gemini failed → fallback to anthropic` warning in the terminal means — it's working as designed.

---

## 9. Team Configuration

API keys are loaded from a `.env` file — never hardcoded. Each team member maintains their own `.env` with their own keys. The `.env` file is in `.gitignore` so keys are never pushed to version control.

```bash
# .env (each person's own file, never shared)
GEMINI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```

---

## 10. File Reference

| File | Role |
|---|---|
| `utils/router.py` | Multi-provider routing, fallback, JSON extraction |
| `utils/gemini.py` | Gemini-specific call wrapper |
| `utils/state.py` | Streamlit session state initializer |
| `agents/planner.py` | Agent 1 — Gemini Flash |
| `agents/researcher.py` | Agent 2 — Gemini Flash |
| `agents/writer.py` | Agent 3 — Claude Sonnet ⭐ |
| `agents/reviewer.py` | Agent 4 — Claude Haiku |
| `app/pipeline.py` | Orchestrator + revision loop |
| `app/main.py` | Streamlit entry point |
| `app/ui.py` | All UI components (sidebar, tabs, results) |
| `app/style.css` | Pixel road-map theme |
| `notebooks/GDD_Creator_Colab.ipynb` | Standalone Colab version |
