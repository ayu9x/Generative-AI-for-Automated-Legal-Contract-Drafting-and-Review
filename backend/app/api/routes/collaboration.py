
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

router = APIRouter(
    prefix="/collaboration",
    tags=["collaboration"]
)

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    status: str  # todo, in_progress, done
    assignee: str
    due_date: Optional[str] = None
    priority: str = "medium"

class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contract_id: str
    user_name: str
    text: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class Activity(BaseModel):
    id: str
    user_name: str
    action: str
    target: str
    timestamp: str
    icon: str = "activity" 

# In-memory store
_tasks: List[Task] = []
_comments: Dict[str, List[Comment]] = {}
_seeded = False

def _seed_collaboration():
    global _seeded
    if _seeded:
        return

    _tasks.extend([
        Task(id="1", title="Review NDA Clauses", status="todo", assignee="Legal Team", priority="high", due_date="2026-03-15"),
        Task(id="2", title="Approve Vendor Agreement", status="in_progress", assignee="John Doe", priority="medium", due_date="2026-03-20"),
        Task(id="3", title="Check Compliance (GDPR)", status="done", assignee="Sarah Smith", priority="high", due_date="2026-03-10"),
    ])
    
    _seeded = True


@router.get("/tasks", response_model=List[Task])
async def list_tasks():
    return _tasks

@router.post("/tasks", response_model=Task)
async def create_task(task: Task):
    _tasks.append(task)
    return task

@router.put("/tasks/{task_id}/status")
async def update_task_status(task_id: str, status: str):
    for task in _tasks:
        if task.id == task_id:
            task.status = status
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@router.get("/comments/{contract_id}", response_model=List[Comment])
async def get_comments(contract_id: str):
    return _comments.get(contract_id, [])

@router.post("/comments", response_model=Comment)
async def add_comment(comment: Comment):
    comment.id = str(uuid.uuid4())
    comment.created_at = datetime.utcnow().isoformat()
    if comment.contract_id not in _comments:
        _comments[comment.contract_id] = []
    _comments[comment.contract_id].append(comment)
    return comment

@router.get("/activity", response_model=List[Activity])
async def get_activity_feed():
    # Return mock feed
    return [
        Activity(id="1", user_name="John Doe", action="edited", target="Service Agreement v2", timestamp=datetime.utcnow().isoformat(), icon="edit"),
        Activity(id="2", user_name="Sarah Smith", action="commented on", target="NDA for Client X", timestamp=datetime.utcnow().isoformat(), icon="message"),
        Activity(id="3", user_name="System", action="completed", target="Compliance Check", timestamp=datetime.utcnow().isoformat(), icon="check"),
    ]
