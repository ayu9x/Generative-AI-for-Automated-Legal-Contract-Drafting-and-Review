
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(
    prefix="/workflows",
    tags=["workflows"]
)

class WorkflowStep(BaseModel):
    id: str
    name: str
    approver_role: str
    condition: Optional[str] = None
    status: str = "pending"  # pending, active, approved, rejected, skipped

class Workflow(BaseModel):
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    contract_id: Optional[str] = None
    status: str = "draft"  # draft, active, completed, terminated
    created_at: str
    updated_at: str

class WorkflowCreate(BaseModel):
    name: str
    description: str
    steps: List[Dict[str, Any]]

# In-memory store
_workflows: Dict[str, Workflow] = {}
_seeded = False

def _seed_workflows():
    global _seeded
    if _seeded:
        return
    
    mock_data = [
        {
            "id": "wf-1",
            "name": "Standard NDA Approval",
            "description": "Standard approval chain for Non-Disclosure Agreements",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "steps": [
                {"id": "s1", "name": "Legal Review", "approver_role": "Legal Associate", "status": "approved"},
                {"id": "s2", "name": "Manager Approval", "approver_role": "Legal Manager", "status": "active"},
                {"id": "s3", "name": "Final Sign-off", "approver_role": "VP Legal", "status": "pending"}
            ]
        },
        {
            "id": "wf-2",
            "name": "High Value Contract (> $50k)",
            "description": "Approval workflow for contracts exceeding $50,000",
            "status": "draft",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "steps": [
                {"id": "s1", "name": "Finance Review", "approver_role": "Finance Manager", "status": "pending"},
                {"id": "s2", "name": "Legal Compliance", "approver_role": "Legal Counsel", "status": "pending"},
                {"id": "s3", "name": "CFO Approval", "approver_role": "CFO", "condition": "value > 100000", "status": "pending"}
            ]
        }
    ]

    for data in mock_data:
        steps = [WorkflowStep(**s) for s in data["steps"]]
        wf = Workflow(**data)
        wf.steps = steps
        _workflows[wf.id] = wf
    
    _seeded = True

@router.on_event("startup")
async def startup_event():
    _seed_workflows()

@router.get("/", response_model=List[Workflow])
async def list_workflows():
    return list(_workflows.values())

@router.post("/", response_model=Workflow)
async def create_workflow(workflow_in: WorkflowCreate):
    wf_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    steps = []
    for s in workflow_in.steps:
        step = WorkflowStep(
            id=str(uuid.uuid4()),
            name=s.get("name", "New Step"),
            approver_role=s.get("approver_role", "Admin"),
            condition=s.get("condition"),
            status="pending"
        )
        steps.append(step)

    new_wf = Workflow(
        id=wf_id,
        name=workflow_in.name,
        description=workflow_in.description,
        steps=steps,
        status="draft",
        created_at=now,
        updated_at=now
    )
    
    _workflows[wf_id] = new_wf
    return new_wf

@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str):
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _workflows[workflow_id]

@router.post("/{workflow_id}/approve-step/{step_id}")
async def approve_step(workflow_id: str, step_id: str):
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    wf = _workflows[workflow_id]
    
    step_found = False
    for step in wf.steps:
        if step.id == step_id:
            step.status = "approved"
            step_found = True
            break
    
    if not step_found:
        raise HTTPException(status_code=404, detail="Step not found")
        
    wf.updated_at = datetime.utcnow().isoformat()
    return wf
