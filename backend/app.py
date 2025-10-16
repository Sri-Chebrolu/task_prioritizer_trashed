from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DATA_PATH = Path(__file__).resolve().parent / "tasks_store.json"
LEGACY_TASKS_PATH = Path(__file__).resolve().parent.parent / "tasks.json"

store_lock = Lock()
tasks_cache: List[dict] = []


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def compute_priority_label(score: int) -> str:
    if score >= 8:
        return "High"
    if score >= 4:
        return "Medium"
    return "Low"


def ensure_datetime(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat() + "Z"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", ""))
        return parsed.replace(microsecond=0).isoformat() + "Z"
    except ValueError:
        return None


def bootstrap_from_legacy() -> List[dict]:
    if not LEGACY_TASKS_PATH.exists():
        return []

    with LEGACY_TASKS_PATH.open("r", encoding="utf-8") as legacy_file:
        try:
            legacy_tasks = legacy_file.read()
        except OSError:
            legacy_tasks = "[]"

    try:
        data = json.loads(legacy_tasks)
    except ValueError:
        data = []

    tasks: List[dict] = []
    for item in data:
        score = item.get("priority score") or item.get("priority_score") or 5
        created_at = ensure_datetime(item.get("created_at")) or utc_now_iso()
        status_updated = ensure_datetime(item.get("status_update_time")) or created_at
        status = (item.get("status") or "Incomplete").lower()
        tasks.append(
            {
                "id": int(item.get("id") or len(tasks) + 1),
                "title": item.get("text") or "Untitled task",
                "description": item.get("text") or "Imported task",
                "category": item.get("category") or "Administrative",
                "priorityScore": int(score),
                "priorityLabel": compute_priority_label(int(score)),
                "status": "completed" if status == "complete" else status,
                "estimatedMinutes": None,
                "scheduledStart": None,
                "scheduledEnd": None,
                "rationale": None,
                "suggestions": [],
                "conflict": False,
                "history": [
                    {
                        "at": created_at,
                        "description": "Imported from legacy tasks.json",
                    }
                ],
                "createdAt": created_at,
                "updatedAt": status_updated,
            }
        )
    return tasks


def ensure_store_exists() -> None:
    if DATA_PATH.exists():
        return
    tasks = bootstrap_from_legacy()
    if not DATA_PATH.parent.exists():
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as target:
        json.dump(tasks, target, indent=2)


def load_store() -> List[dict]:
    ensure_store_exists()
    with DATA_PATH.open("r", encoding="utf-8") as source:
        try:
            tasks = json.load(source)
        except ValueError:
            tasks = []
    normalised = []
    for task in tasks:
        score = int(task.get("priorityScore") or 5)
        normalised.append(
            {
                **task,
                "priorityScore": score,
                "priorityLabel": compute_priority_label(score),
                "createdAt": ensure_datetime(task.get("createdAt")) or utc_now_iso(),
                "updatedAt": ensure_datetime(task.get("updatedAt")) or utc_now_iso(),
                "scheduledStart": ensure_datetime(task.get("scheduledStart")),
                "scheduledEnd": ensure_datetime(task.get("scheduledEnd")),
            }
        )
    return normalised


def save_store() -> None:
    if not DATA_PATH.parent.exists():
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as target:
        json.dump(tasks_cache, target, indent=2)


tasks_cache = load_store()


class HistoryEntry(BaseModel):
    description: str
    at: Optional[datetime] = None


class TaskCreate(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    category: Optional[str] = "Administrative"
    priority_score: Optional[int] = Field(5, alias="priorityScore", ge=0, le=10)
    status: Optional[str] = "processing"
    estimated_minutes: Optional[int] = Field(30, alias="estimatedMinutes", ge=0)
    scheduled_start: Optional[datetime] = Field(None, alias="scheduledStart")
    scheduled_end: Optional[datetime] = Field(None, alias="scheduledEnd")
    rationale: Optional[str] = None
    suggestions: Optional[List[str]] = Field(default_factory=list)
    conflict: Optional[bool] = False

    class Config:
        populate_by_name = True


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority_score: Optional[int] = Field(None, alias="priorityScore", ge=0, le=10)
    status: Optional[str] = None
    estimated_minutes: Optional[int] = Field(None, alias="estimatedMinutes", ge=0)
    scheduled_start: Optional[datetime] = Field(None, alias="scheduledStart")
    scheduled_end: Optional[datetime] = Field(None, alias="scheduledEnd")
    rationale: Optional[str] = None
    suggestions: Optional[List[str]] = Field(default=None)
    conflict: Optional[bool] = None
    history_entry: Optional[HistoryEntry] = Field(None, alias="historyEntry")

    class Config:
        populate_by_name = True


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    priorityScore: int
    priorityLabel: str
    status: str
    estimatedMinutes: Optional[int]
    scheduledStart: Optional[datetime]
    scheduledEnd: Optional[datetime]
    rationale: Optional[str]
    suggestions: List[str]
    conflict: bool
    history: List[HistoryEntry]
    createdAt: datetime
    updatedAt: datetime

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat().replace("+00:00", "Z")}


app = FastAPI(title="PriorityOS Mock API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
    ,
    allow_headers=["*"],
)


@app.get("/api/health")
def healthcheck() -> dict:
    return {"status": "ok", "time": utc_now_iso()}


@app.get("/api/tasks", response_model=List[TaskResponse])
def list_tasks() -> List[TaskResponse]:
    with store_lock:
        ordered = sorted(
            tasks_cache,
            key=lambda task: (-int(task.get("priorityScore", 0)), task.get("title", ""))
        )
        return [TaskResponse.parse_obj(task) for task in ordered]


def next_task_id() -> int:
    existing_ids = {task["id"] for task in tasks_cache}
    candidate = max(existing_ids, default=0) + 1
    while candidate in existing_ids:
        candidate += 1
    return candidate


@app.post("/api/tasks", response_model=TaskResponse, status_code=201)
def create_task(payload: TaskCreate) -> TaskResponse:
    with store_lock:
        task_id = payload.id
        existing_ids = {task["id"] for task in tasks_cache}
        if task_id is None or task_id in existing_ids:
            task_id = next_task_id()

        now_iso = utc_now_iso()
        score = payload.priority_score or 5
        task = {
            "id": task_id,
            "title": payload.title,
            "description": payload.description or payload.title,
            "category": payload.category or "Administrative",
            "priorityScore": score,
            "priorityLabel": compute_priority_label(score),
            "status": (payload.status or "processing").lower(),
            "estimatedMinutes": payload.estimated_minutes,
            "scheduledStart": ensure_datetime(payload.scheduled_start),
            "scheduledEnd": ensure_datetime(payload.scheduled_end),
            "rationale": payload.rationale,
            "suggestions": payload.suggestions or [],
            "conflict": bool(payload.conflict),
            "history": [
                {
                    "at": now_iso,
                    "description": "Task captured through API",
                }
            ],
            "createdAt": now_iso,
            "updatedAt": now_iso,
        }
        tasks_cache.append(task)
        save_store()
        return TaskResponse.parse_obj(task)


@app.patch("/api/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate) -> TaskResponse:
    with store_lock:
        for index, task in enumerate(tasks_cache):
            if task["id"] != task_id:
                continue

            updates = payload.dict(exclude_unset=True, by_alias=True)
            score = updates.get("priorityScore")
            if score is not None:
                task["priorityScore"] = int(score)
                task["priorityLabel"] = compute_priority_label(int(score))
            if updates.get("title"):
                task["title"] = updates["title"]
            if updates.get("description"):
                task["description"] = updates["description"]
            if updates.get("category"):
                task["category"] = updates["category"]
            if updates.get("status"):
                task["status"] = updates["status"].lower()
            if "estimatedMinutes" in updates:
                task["estimatedMinutes"] = updates["estimatedMinutes"]
            if "scheduledStart" in updates:
                task["scheduledStart"] = ensure_datetime(updates["scheduledStart"])
            if "scheduledEnd" in updates:
                task["scheduledEnd"] = ensure_datetime(updates["scheduledEnd"])
            if "rationale" in updates:
                task["rationale"] = updates["rationale"]
            if "suggestions" in updates and updates["suggestions"] is not None:
                task["suggestions"] = updates["suggestions"]
            if updates.get("conflict") is not None:
                task["conflict"] = bool(updates["conflict"])
            if payload.history_entry:
                entry_time = ensure_datetime(payload.history_entry.at) or utc_now_iso()
                task.setdefault("history", []).append(
                    {
                        "at": entry_time,
                        "description": payload.history_entry.description,
                    }
                )
            task["updatedAt"] = utc_now_iso()
            tasks_cache[index] = task
            save_store()
            return TaskResponse.parse_obj(task)

    raise HTTPException(status_code=404, detail="Task not found")


@app.post("/api/tasks/{task_id}/auto_schedule", response_model=TaskResponse)
def auto_schedule(task_id: int, minutes: int = 30) -> TaskResponse:
    with store_lock:
        task = next((item for item in tasks_cache if item["id"] == task_id), None)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        work_start = datetime.utcnow().replace(hour=8, minute=0, second=0, microsecond=0)
        work_end = work_start.replace(hour=18)
        occupied = []
        for existing in tasks_cache:
            start_iso = ensure_datetime(existing.get("scheduledStart"))
            end_iso = ensure_datetime(existing.get("scheduledEnd"))
            if not start_iso or not end_iso:
                continue
            start_dt = datetime.fromisoformat(start_iso.replace("Z", ""))
            end_dt = datetime.fromisoformat(end_iso.replace("Z", ""))
            occupied.append((start_dt, end_dt))
        candidate = work_start
        duration = timedelta(minutes=minutes or task.get("estimatedMinutes") or 30)
        while candidate + duration <= work_end:
            candidate_end = candidate + duration
            overlaps = any(
                start < candidate_end and end > candidate
                for start, end in occupied
            )
            if not overlaps:
                break
            candidate = candidate + timedelta(minutes=30)

        task["scheduledStart"] = ensure_datetime(candidate)
        task["scheduledEnd"] = ensure_datetime(candidate + duration)
        task["status"] = "scheduled"
        task.setdefault("history", []).append(
            {
                "at": utc_now_iso(),
                "description": "Auto-scheduled via backend endpoint",
            }
        )
        task["updatedAt"] = utc_now_iso()
        save_store()
        return TaskResponse.parse_obj(task)
