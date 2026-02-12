
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(
    prefix="/drive",
    tags=["drive"]
)

class DriveItem(BaseModel):
    id: str
    name: str
    type: str  # folder, file
    parent_id: Optional[str] = None
    size: Optional[str] = None
    modified_at: str
    owner: str
    starred: bool = False

# In-memory store
_drive_items: List[DriveItem] = []
_seeded = False

def _seed_drive():
    global _seeded
    if _seeded:
        return

    now = datetime.utcnow().isoformat()
    # Folders
    _drive_items.append(DriveItem(id="root", name="My Drive", type="folder", modified_at=now, owner="me")) # logical root, usually hidden or implicit
    
    _drive_items.append(DriveItem(id="f1", name="Contracts 2024", type="folder", parent_id=None, modified_at=now, owner="me"))
    _drive_items.append(DriveItem(id="f2", name="Templates", type="folder", parent_id=None, modified_at=now, owner="me"))
    _drive_items.append(DriveItem(id="f3", name="Archived", type="folder", parent_id=None, modified_at=now, owner="System"))

    # Files
    _drive_items.append(DriveItem(id="d1", name="NDA_Google.pdf", type="file", parent_id="f1", size="2.4 MB", modified_at=now, owner="me"))
    _drive_items.append(DriveItem(id="d2", name="Service_Agreement_v1.docx", type="file", parent_id="f1", size="1.1 MB", modified_at=now, owner="me"))
    _drive_items.append(DriveItem(id="d3", name="Employment_Template.docx", type="file", parent_id="f2", size="500 KB", modified_at=now, owner="Admin"))

    _seeded = True

@router.on_event("startup")
async def startup_event():
    _seed_drive()

@router.get("/files", response_model=List[DriveItem])
async def list_files(parent_id: Optional[str] = None):
    # If parent_id is None, return root-level items (where parent_id is None)
    return [item for item in _drive_items if item.parent_id == parent_id]

@router.post("/folder", response_model=DriveItem)
async def create_folder(name: str, parent_id: Optional[str] = None):
    new_folder = DriveItem(
        id=str(uuid.uuid4()),
        name=name,
        type="folder",
        parent_id=parent_id,
        modified_at=datetime.utcnow().isoformat(),
        owner="me"
    )
    _drive_items.append(new_folder)
    return new_folder

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), parent_id: Optional[str] = None):
    # Mock upload
    new_file = DriveItem(
        id=str(uuid.uuid4()),
        name=file.filename,
        type="file",
        parent_id=parent_id,
        size=f"{file.size or 0/1024:.1f} KB",
        modified_at=datetime.utcnow().isoformat(),
        owner="me"
    )
    _drive_items.append(new_file)
    return new_file

@router.delete("/{item_id}")
async def delete_item(item_id: str):
    global _drive_items
    _drive_items = [item for item in _drive_items if item.id != item_id]
    return {"status": "deleted"}
