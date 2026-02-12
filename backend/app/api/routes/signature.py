
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(
    prefix="/signature",
    tags=["signature"]
)

class SignatureAudit(BaseModel):
    id: str
    action: str
    user: str
    timestamp: str
    ip_address: str
    details: str

class SignatureRequest(BaseModel):
    contract_id: str
    signer_name: str
    signature_data: str  # Base64 string
    font_style: Optional[str] = None

# In-memory store
_signatures: Dict[str, Dict] = {}
_audit_logs: Dict[str, List[SignatureAudit]] = {}

@router.post("/sign")
async def sign_contract(req: SignatureRequest):
    sign_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Store signature (mock)
    _signatures[sign_id] = {
        "contract_id": req.contract_id,
        "signer_name": req.signer_name,
        "signature_data": req.signature_data[:50] + "...", # Truncate for log
        "timestamp": timestamp,
        "status": "signed"
    }
    
    # Add audit log
    audit_entry = SignatureAudit(
        id=str(uuid.uuid4()),
        action="CONTRACT_SIGNED",
        user=req.signer_name,
        timestamp=timestamp,
        ip_address="192.168.1.1", # Mock IP
        details=f"Digitally signed by {req.signer_name} using secure e-signature."
    )
    
    if req.contract_id not in _audit_logs:
        _audit_logs[req.contract_id] = []
    
    _audit_logs[req.contract_id].append(audit_entry)
    
    return {
        "status": "success",
        "signature_id": sign_id,
        "message": "Contract signed successfully",
        "timestamp": timestamp
    }

@router.get("/audit/{contract_id}", response_model=List[SignatureAudit])
async def get_audit_trail(contract_id: str):
    # Return mock audit trail if not found (for demo purposes)
    if contract_id not in _audit_logs:
        return [
            SignatureAudit(
                id=str(uuid.uuid4()),
                action="CONTRACT_VIEWED",
                user="System",
                timestamp=datetime.utcnow().isoformat(),
                ip_address="192.168.1.1",
                details="Contract opened for signing"
            )
        ]
    return _audit_logs[contract_id]

@router.get("/verify/{signature_id}")
async def verify_signature(signature_id: str):
    if signature_id not in _signatures:
        raise HTTPException(status_code=404, detail="Signature not found")
    
    sig = _signatures[signature_id]
    return {
        "valid": True,
        "signer": sig["signer_name"],
        "timestamp": sig["timestamp"],
        "certificate_authority": "LegalAI Trust CA (Demo)"
    }
