import html
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config import UPLOADS_DIR

def format_telegram_response(analysis: Dict[str, Any], query_id: Optional[int] = None) -> str:
    """
    Formats the AI analysis into clean, precise, and readable HTML for Telegram.
    Simple, elegant structure: direct answer + commands + pro-tip.
    """
    category = html.escape(str(analysis.get("category", "FOSS Mentor")), quote=False)
    subcategory = html.escape(str(analysis.get("subcategory", "")), quote=False)
    direct_answer = str(analysis.get("direct_answer", "")).strip()
    code = str(analysis.get("terminal_commands_or_code", "")).strip()
    tip = html.escape(str(analysis.get("foss_tip", "")), quote=False).strip()

    cat_badge = f"{category} • {subcategory}" if subcategory and subcategory not in ["General", "Welcome", ""] else category

    parts = [f"🐧 <b>FOSS MBCCET</b> | <i>{cat_badge}</i>\n"]

    if direct_answer:
        parts.append(direct_answer)

    if code:
        escaped_code = html.escape(code, quote=False)
        parts.append(f"\n💻 <b>Commands:</b>\n<pre><code>{escaped_code}</code></pre>")

    if tip:
        parts.append(f"\n💡 <i>Tip: {tip}</i>")

    return "\n".join(parts)

def generate_pdf_report(
    analysis: Dict[str, Any],
    query_text: str,
    output_filename: Optional[str] = None,
    student_name: str = "FOSS MBCCET Member"
) -> str:
    """
    Generates a PDF diagnostic and learning cheat sheet using ReportLab.
    Falls back to a structured Markdown summary if ReportLab is not installed.
    """
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"foss_diagnostic_{timestamp}.pdf"

    output_path = UPLOADS_DIR / output_filename

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Preformatted
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'FOSSTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=6
        )

        meta_style = ParagraphStyle(
            'FOSSMeta',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=12
        )

        h2_style = ParagraphStyle(
            'FOSSH2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            textColor=colors.HexColor('#0F766E'),
            spaceBefore=10,
            spaceAfter=4
        )

        body_style = ParagraphStyle(
            'FOSSBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#334155'),
            spaceAfter=8
        )

        code_style = ParagraphStyle(
            'FOSSCode',
            parent=styles['Code'],
            fontName='Courier',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#0F172A'),
            backColor=colors.HexColor('#F1F5F9'),
            borderPadding=8,
            spaceBefore=4,
            spaceAfter=8
        )

        elements = []

        # Header
        elements.append(Paragraph(f"{COMMUNITY_NAME} • Technical Resolution Report", title_style))
        elements.append(Paragraph(f"Recipient: {student_name} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0D9488'), spaceAfter=14))

        # Query Overview
        elements.append(Paragraph("1. Student Inquiry / Problem Statement", h2_style))
        elements.append(Paragraph(f"<b>Query:</b> {html.escape(query_text)}", body_style))
        elements.append(Paragraph(f"<b>Category:</b> {analysis.get('category')} ({analysis.get('subcategory')}) | <b>Level:</b> {analysis.get('difficulty')}", meta_style))

        # Explanation
        elements.append(Paragraph("2. Conceptual Breakdown & Resolution", h2_style))
        for para in analysis.get('direct_answer', '').split('\n\n'):
            if para.strip():
                elements.append(Paragraph(html.escape(para.strip()).replace('\n', '<br/>'), body_style))

        # Code & Commands
        code_text = analysis.get('terminal_commands_or_code', '')
        if code_text and code_text.strip():
            elements.append(Paragraph("3. Runnable Terminal Commands / Code Patch", h2_style))
            elements.append(Preformatted(code_text, code_style))

        # Pro-Tip & Tools
        elements.append(Paragraph("4. Recommended Open Source Tools & Hacker Pro-Tip", h2_style))
        tools_str = ", ".join(analysis.get('recommended_foss_tools', []))
        elements.append(Paragraph(f"<b>FOSS Ecosystem Tools:</b> {tools_str}", body_style))
        elements.append(Paragraph(f"<b>🐧 Community Pro-Tip:</b> {html.escape(analysis.get('foss_tip', ''))}", body_style))

        # Footer
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=8))
        elements.append(Paragraph("FOSS MBCCET - Empowering Students with Open Source Software Freedom", meta_style))

        doc.build(elements)
        return str(output_path)

    except ImportError:
        # Fallback to saving a clean markdown diagnostic file
        md_filename = output_path.with_suffix('.md')
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(f"# {COMMUNITY_NAME} • Diagnostic Report\n\n")
            f.write(f"**Student:** {student_name}\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Problem Statement\n{query_text}\n\n")
            f.write(f"**Category:** {analysis.get('category')} ({analysis.get('subcategory')})\n")
            f.write(f"**Difficulty:** {analysis.get('difficulty')}\n\n")
            f.write(f"## Solution\n{analysis.get('direct_answer')}\n\n")
            f.write(f"## Terminal Commands / Code\n```bash\n{analysis.get('terminal_commands_or_code')}\n```\n\n")
            f.write(f"## Recommended Tools\n{', '.join(analysis.get('recommended_foss_tools', []))}\n\n")
            f.write(f"**FOSS Tip:** {analysis.get('foss_tip')}\n")
        return str(md_filename)
