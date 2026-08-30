import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from backend.app.api.auth import get_current_user

router = APIRouter(prefix="/email", tags=["email"])
logger = logging.getLogger("hres.email")

class EmailSendRequest(BaseModel):
    recipients: List[str]
    subject: str
    body: str
    incident_id: Optional[str] = None

@router.post("/send")
def send_email(req: EmailSendRequest, user: dict = Depends(get_current_user)):
    """Send a custom email from the UI, optionally attaching an AAR report."""
    from backend.app.services.email_service import send_custom_email
    
    # If an incident_id is provided, try to fetch its AAR content
    aar_content = None
    if req.incident_id:
        from backend.app.repositories.database import get_db_connection
        conn, dialect = get_db_connection()
        cursor = conn.cursor()
        try:
            if dialect == "postgres":
                cursor.execute("SELECT content FROM after_action_reports WHERE incident_id = %s", (req.incident_id,))
            else:
                cursor.execute("SELECT content FROM after_action_reports WHERE incident_id = ?", (req.incident_id,))
            row = cursor.fetchone()
            if row:
                aar_content = row[0]
        finally:
            conn.close()

    success = send_custom_email(
        subject=req.subject,
        body=req.body,
        recipients=req.recipients,
        aar_content=aar_content,
        incident_id=req.incident_id
    )
    
    if not success:
        raise HTTPException(500, "Failed to send email. Check SMTP configuration.")
    return {"message": "Email sent successfully."}
