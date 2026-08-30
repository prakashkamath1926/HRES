from fastapi import APIRouter, HTTPException, Response
from backend.app.repositories.reports import get_after_action_report
import logging

logger = logging.getLogger("hres.reports")
router = APIRouter(prefix="/incidents", tags=["reports"])


@router.get("/{incident_id}/aar")
def get_after_action_report_endpoint(incident_id: str):
    """
    Download AAR as PDF (fpdf2 v2.x) or formatted HTML fallback.
    """
    report = get_after_action_report(incident_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail="After-Action Report not generated yet. Please resolve the incident first."
        )

    content = report["content"]
    generated_at = report.get("generated_at", "")

    try:
        from fpdf import FPDF

        # ── Build PDF ──────────────────────────────────────────────────────────
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_margins(left=15, top=15, right=15)
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        # ── Header bar ────────────────────────────────────────────────────────
        pdf.set_fill_color(13, 21, 38)
        pdf.rect(0, 0, 210, 28, style="F")
        pdf.set_y(7)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(232, 240, 254)
        pdf.cell(0, 10, "AFTER-ACTION REPORT", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(160, 180, 210)
        pdf.cell(0, 5, f"HRES Heat Response Emergency System  |  Incident: {incident_id}", align="C", new_x="LMARGIN", new_y="NEXT")

        # ── Meta line ─────────────────────────────────────────────────────────
        pdf.set_y(34)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 120, 150)
        pdf.cell(0, 5, f"Generated: {generated_at[:19] if generated_at else 'N/A'}  |  Classification: CONFIDENTIAL", align="C", new_x="LMARGIN", new_y="NEXT")

        # ── Divider ───────────────────────────────────────────────────────────
        pdf.set_y(42)
        pdf.set_draw_color(56, 89, 140)
        pdf.set_line_width(0.5)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(6)

        # ── Body content ──────────────────────────────────────────────────────
        # Encode to latin-1 safely (fpdf2 built-in fonts are latin-1)
        safe_content = content.encode("latin-1", errors="replace").decode("latin-1")

        for line in safe_content.split("\n"):
            line = line.rstrip()

            if not line:
                pdf.ln(3)
                continue

            # Section headers: lines that start with === or are fully uppercase 5+ chars
            stripped = line.strip()
            if stripped.startswith("===") and stripped.endswith("==="):
                pdf.ln(2)
                pdf.set_fill_color(20, 30, 55)
                pdf.set_text_color(100, 160, 255)
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 8, stripped.strip("= "), fill=True, new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(40, 50, 65)
                pdf.ln(1)

            elif stripped.isupper() and len(stripped) > 8 and not stripped.startswith("-"):
                # All-caps section title
                pdf.ln(2)
                pdf.set_text_color(59, 130, 246)
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 7, stripped, new_x="LMARGIN", new_y="NEXT")
                pdf.set_draw_color(59, 130, 246)
                pdf.set_line_width(0.3)
                y = pdf.get_y()
                pdf.line(15, y, 195, y)
                pdf.ln(3)
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(40, 50, 65)

            elif stripped.startswith(("-", "•", "*")):
                # Bullet point
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(60, 70, 90)
                pdf.set_x(20)
                pdf.multi_cell(170, 5, "  " + stripped, new_x="LMARGIN", new_y="NEXT")

            elif stripped[0].isdigit() and len(stripped) > 2 and stripped[1] in (".", ")"):
                # Numbered list
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(60, 70, 90)
                pdf.set_x(20)
                pdf.multi_cell(170, 5, stripped, new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)

            else:
                # Normal paragraph text
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(40, 50, 65)
                pdf.multi_cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")

        # ── Footer ────────────────────────────────────────────────────────────
        pdf.set_y(-18)
        pdf.set_draw_color(56, 89, 140)
        pdf.set_line_width(0.3)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(2)
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(120, 130, 150)
        pdf.cell(0, 5,
            f"Page 1  |  Incident {incident_id}  |  HRES Platform  |  Confidential",
            align="C"
        )

        # ── Output ────────────────────────────────────────────────────────────
        pdf_bytes = bytes(pdf.output())
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="HRES_AAR_{incident_id[:16]}.pdf"',
                "Cache-Control": "no-cache, no-store",
                "X-Content-Type-Options": "nosniff",
            }
        )

    except ImportError:
        logger.warning("fpdf2 not installed. Returning printable HTML.")
        return _html_fallback(incident_id, content, generated_at)

    except Exception as e:
        logger.error(f"AAR PDF generation failed: {e}", exc_info=True)
        # Fall back to HTML on any PDF error
        return _html_fallback(incident_id, content, generated_at)


def _html_fallback(incident_id: str, content: str, generated_at: str) -> Response:
    """Return a nicely formatted, printable HTML page as AAR fallback."""
    html_lines = []
    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            html_lines.append("<br/>")
        elif stripped.startswith("===") and stripped.endswith("==="):
            html_lines.append(f"<h2 style='color:#3b82f6;border-bottom:1px solid #38598c;padding-bottom:4px;margin-top:20px'>{stripped.strip('= ')}</h2>")
        elif stripped.isupper() and len(stripped) > 8:
            html_lines.append(f"<h3 style='color:#60a5fa;margin-top:16px'>{stripped}</h3>")
        elif stripped.startswith(("-", "•", "*")):
            html_lines.append(f"<li style='margin:3px 0;'>{stripped.lstrip('-•* ')}</li>")
        else:
            html_lines.append(f"<p style='margin:4px 0;line-height:1.6;'>{line}</p>")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>HRES AAR — {incident_id}</title>
  <style>
    body {{font-family:Arial,sans-serif;max-width:900px;margin:40px auto;padding:20px;color:#1f2937;background:#f9fafb;}}
    .header {{background:#0d1526;color:#e8f0fe;padding:20px;border-radius:8px;text-align:center;margin-bottom:24px;}}
    .header h1 {{margin:0 0 6px;font-size:22px;}}
    .header p {{margin:0;color:#a0b4d2;font-size:12px;}}
    .content {{background:#fff;padding:24px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.08);}}
    ul {{padding-left:20px;}}
    @media print {{body{{margin:0;background:white;}} .header{{-webkit-print-color-adjust:exact;print-color-adjust:exact;}}}}
  </style>
</head>
<body>
  <div class="header">
    <h1>AFTER-ACTION REPORT</h1>
    <p>HRES Heat Response Emergency System &nbsp;|&nbsp; Incident: {incident_id} &nbsp;|&nbsp; {generated_at[:19] if generated_at else ''}</p>
  </div>
  <div class="content">{''.join(html_lines)}</div>
</body>
</html>"""

    return Response(
        content=html.encode("utf-8"),
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="HRES_AAR_{incident_id[:16]}.html"',
        }
    )
