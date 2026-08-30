import os
import resend
import logging
from backend.app.core.config import settings
from typing import List, Optional

logger = logging.getLogger(__name__)

def send_incident_report_email(incident_id: str, severity: str, report_content: str, recipients: List[str]):
    """
    Sends an automated incident report via Resend.
    """
    api_key = settings.RESEND_API_KEY or os.environ.get("RESEND_API_KEY")
    if not api_key:
        logger.warning(f"Resend API key is not configured. Skipping email for incident {incident_id}.")
        return False

    resend.api_key = api_key
    subject = f"HRES Alert: {severity} Incident {incident_id}"
    
    html = f"""\
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #d9534f;">HRES Automated Alert</h2>
        <p><strong>Incident ID:</strong> {incident_id}</p>
        <p><strong>Severity:</strong> {severity}</p>
        <hr>
        <h3>After-Action Report & Operational Guidance</h3>
        <pre style="white-space: pre-wrap; font-family: inherit; background: #f9f9f9; padding: 15px; border-left: 4px solid #d9534f;">{report_content}</pre>
        <hr>
        <p style="font-size: 12px; color: #888;">This is an automated message from the Heat Response Emergency System (HRES).</p>
      </body>
    </html>
    """

    try:
        r = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": recipients,
            "subject": subject,
            "html": html,
            "text": report_content
        })
        logger.info(f"Successfully sent incident report for {incident_id} to {recipients}. Resend ID: {r.get('id')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email for incident {incident_id}: {e}")
        return False

def send_custom_email(subject: str, body: str, recipients: List[str], aar_content: Optional[str] = None, incident_id: Optional[str] = None):
    """
    Sends a custom email via Resend, optionally attaching the AAR report.
    """
    api_key = settings.RESEND_API_KEY or os.environ.get("RESEND_API_KEY")
    if not api_key:
        logger.warning("Resend API key is not configured. Skipping custom email.")
        return False

    resend.api_key = api_key
    payload = {
        "from": "onboarding@resend.dev",
        "to": recipients,
        "subject": subject,
        "html": f"<p>{body}</p>",
        "text": body
    }

    # Optionally attach AAR content as a text file
    if aar_content and incident_id:
        payload["attachments"] = [
            {
                "filename": f"AAR_Report_{incident_id}.txt",
                "content": list(aar_content.encode("utf-8"))
            }
        ]

    try:
        r = resend.Emails.send(payload)
        logger.info(f"Successfully sent custom email '{subject}' to {recipients}. Resend ID: {r.get('id')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send custom email: {e}")
        return False
