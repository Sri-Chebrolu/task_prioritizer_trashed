TRASHED

# task_prioritizer
Small project to create AI personal assistant

# AI-Powered Task Scheduling Assistant

PriorityOS is an AI-native productivity tool that helps you **turn your mental clutter into an executable schedule**. Just dump your tasks in plain language, and PriorityOS will automatically **parse, prioritize, and schedule them into your calendar** based on your availability and preferences.

---

## Problem

Modern professionals are overwhelmed by scattered tasks spread across notes, messages, and memory. Traditional to-do lists help capture tasks but don't help you **act** on them. Manual prioritization and scheduling are mentally draining and often skipped—leading to missed deadlines, burnout, and underperformance.

---

## Solution

PriorityOS acts like your personal executive assistant. It:
- Accepts freeform task input (e.g. “email Sarah, finish report, book dentist”)
- Automatically structures and ranks tasks based on urgency, time sensitivity, and user-defined preferences
- Schedules them directly into your calendar (Google Calendar support in MVP)
- Adapts when your day shifts and lets you re-prioritize on the fly

---

## MVP Features

- 📝 **Task Dump Input** – Write or paste tasks into a single field  
- ⚙️ **AI Task Parser** – Parses and structures raw tasks  
- 📊 **Smart Prioritization** – Assigns urgency and duration using LLMs  
- 📆 **Calendar Scheduling** – Auto-places tasks into your day  
- 🧲 **Drag-and-Drop Edits** – Full manual override when needed  
- 📱 **Cross-Platform Access** – Works across desktop and mobile

---

## Status

🚧 *This is an active work-in-progress.*  
Initial MVP planning and design phases are complete. Development is beginning now.

---

## 🔄 User Flow

1. **Task Dump** – Enter freeform tasks into a text field
2. **Parsing** – AI converts the dump into structured tasks
3. **Prioritization** – Tasks are ranked and estimated
4. **Scheduling** – Tasks are time-blocked into your calendar
5. **Review & Execute** – User edits schedule and gets to work

---

## 📁 Project Structure

- `task_prioritizer.py` – CLI harness combining the LLM agent with task storage
- `tasks.json` – Simple JSON store for tasks
- `system_prompt.md` – LLM system prompt the agent loads on startup
- `design.md` – Product & UX design reference
- `backend/` – FastAPI mock service that exposes the task list over HTTP
- `frontend/` – Interactive front-end mock for the PriorityOS UI

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+

### Run the CLI assistant

1. Create a virtual environment using `python3 -m venv .venv`
2. Activate it with `source .venv/bin/activate`
3. Install the dependencies (see `requirements.txt` once published)
4. Configure your Ollama model (the code expects `llama3.2:3b`)
5. Run `python task_prioritizer.py`

### Front-end prototype

The `/frontend` directory ships an interactive, client-side mock that mirrors the UI architecture documented in `design.md`.

1. Open `frontend/index.html` directly in a browser, or serve the folder locally with `python -m http.server` if you prefer `http://localhost`.
2. When served from `http://localhost`, the UI calls the FastAPI backend at `http://localhost:8000/api`. If the backend is offline, it gracefully falls back to the built-in seed data so the prototype still works.
3. Interact with priority/category filters, mark tasks complete, auto-schedule unslotted work, resolve mocked conflicts, and inspect the task drawer.
4. Use keyboard shortcut `c` to open the capture modal, add tasks with quick syntax (`#category`, `!priority`, `@due`), and hit `Esc` to dismiss overlays.

### Mock backend service

The FastAPI server in `backend/` persists tasks to `backend/tasks_store.json` and mirrors the shapes used by the UI. To run it locally:

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

Endpoints exposed under `http://localhost:8000/api`:

- `GET /tasks` – list tasks ordered by priority
- `POST /tasks` – create a new task entry (accepts the same shape emitted by the UI)
- `PATCH /tasks/{id}` – update status, scheduling metadata, or rationale
- `POST /tasks/{id}/auto_schedule` – demo auto-scheduling heuristic (used when the UI is online)

### Front-end tests

End-to-end UI smoke tests live under `frontend/tests` (Playwright). Run them after installing Playwright:

```bash
cd frontend/tests
npm install --save-dev @playwright/test
npx playwright install
npx playwright test
```

The Playwright config spins up `python -m http.server 4173` automatically and navigates to `http://localhost:4173/frontend/index.html`.
The UI falls back to the local seed data during test runs, so the FastAPI backend does not need to be running for these checks.

---

## 🧠 System Prompt Customization

Update `system_prompt.md` to adjust the agent’s behavior. Restart the CLI to load changes.

---

## 🗺️ Roadmap

- Build FastAPI backend with task ingestion endpoints
- Persist tasks in PostgreSQL and sync with Google Calendar
- Wire the front-end prototype to the real APIs
- Expand agent tooling (conflict resolution, recurring tasks)
