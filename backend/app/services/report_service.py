from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.analytics.service import admin_dashboard, faculty_dashboard


def _safe(value: Any) -> str:
    return str(value if value is not None else "").encode("latin-1", "replace").decode("latin-1")


def _filter_text(filters: dict[str, Any]) -> str:
    parts = []
    for key, label in (
        ("academic_year", "Academic year"),
        ("semester_number", "Semester"),
        ("subject_code", "Subject"),
        ("faculty_id", "Faculty ID"),
    ):
        if filters.get(key):
            parts.append(f"{label}: {filters[key]}")
    return "; ".join(parts) if parts else "All available data"


def build_faculty_report(
    conn,
    faculty_id: int,
    *,
    academic_year: str | None,
    semester_number: int | None,
    subject_code: str | None,
    fmt: str,
) -> tuple[bytes, str, str]:
    data = faculty_dashboard(
        conn,
        faculty_id,
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
    )
    faculty = data.get("faculty") or {}
    if not faculty:
        with conn.cursor() as cur:
            cur.execute("SELECT name, email FROM faculty WHERE faculty_id = %s", (faculty_id,))
            faculty = cur.fetchone() or {}
    name = faculty.get("name", "Faculty")
    filters = data["filters"]
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    filename = f"faculty-performance-{faculty_id}-{stamp}.{fmt}"
    if fmt == "csv":
        return _faculty_csv(data, faculty), "text/csv; charset=utf-8", filename
    return _faculty_pdf(data, faculty), "application/pdf", filename


def build_admin_report(
    conn,
    *,
    academic_year: str | None,
    semester_number: int | None,
    subject_code: str | None,
    faculty_id: int | None,
    fmt: str,
) -> tuple[bytes, str, str]:
    data = admin_dashboard(
        conn,
        academic_year=academic_year,
        semester_number=semester_number,
        subject_code=subject_code,
        faculty_id=faculty_id,
    )
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    filters = data["filters"]
    filename = f"department-analytics-{stamp}.{fmt}"
    if fmt == "csv":
        return _admin_csv(data, filters), "text/csv; charset=utf-8", filename
    return _admin_pdf(data, filters), "application/pdf", filename


def _faculty_csv(data: dict[str, Any], faculty: dict[str, Any]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["FacultyInsight AI - Faculty Performance Report"])
    writer.writerow(["Faculty", faculty.get("name", "")])
    writer.writerow(["Facility ID", faculty.get("faculty_id", "")])
    writer.writerow(["Filters", _filter_text(data["filters"])])
    writer.writerow(["Overall average", data["overall"]["average_rating"]])
    writer.writerow(["Responses", data["overall"]["response_count"]])
    writer.writerow(["Privacy", "Anonymous feedback. No student identifiers are included."])
    writer.writerow([])
    writer.writerow(["Question-wise ratings"])
    writer.writerow(["Question", "Average", "Ratings"])
    for row in data["question_stats"]:
        writer.writerow([row["question_text"], row["average_rating"], row["response_count"]])
    writer.writerow([])
    writer.writerow(["Subject summary"])
    writer.writerow(["Subject code", "Subject", "Semester", "Average", "Responses"])
    for row in data["subject_summary"]:
        writer.writerow([row["subject_code"], row["subject_name"], row["semester_number"], row["average_rating"], row["response_count"]])
    writer.writerow([])
    writer.writerow(["Rating distribution"])
    writer.writerow(["Rating", "Label", "Count", "Percent"])
    for row in data["rating_distribution"]:
        writer.writerow([row["rating"], row["label"], row["count"], row["percentage"]])
    writer.writerow([])
    writer.writerow(["Academic-year trend (same faculty only)"])
    writer.writerow(["Academic year", "Average", "Responses"])
    for row in data["trend"]:
        writer.writerow([row["academic_year"], row["average_rating"], row["response_count"]])
    writer.writerow([])
    writer.writerow(["Evidence-based strengths"])
    for row in data["strengths"]:
        writer.writerow([row["title"], row["evidence"]])
    writer.writerow(["Evidence-based improvement areas"])
    for row in data["improvement_areas"]:
        writer.writerow([row["title"], row["evidence"]])
    writer.writerow([])
    writer.writerow(["Anonymous comments"])
    writer.writerow(["Subject", "Academic year", "Comment", "Sentiment", "Confidence"])
    for row in data["comments"]:
        writer.writerow([
            row["subject_code"],
            row["academic_year"],
            row["comment"],
            row["sentiment"]["label"],
            row["sentiment"]["confidence"],
        ])
    writer.writerow([])
    writer.writerow(["Sentiment method", data["sentiment"]["summary"]["method"]])
    writer.writerow(["Sentiment limitation", data["sentiment"]["summary"]["limitations"]])
    return output.getvalue().encode("utf-8")


def _admin_csv(data: dict[str, Any], filters: dict[str, Any]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["FacultyInsight AI - Department Analytics Report"])
    writer.writerow(["Filters", _filter_text(filters)])
    writer.writerow(["Privacy", "Aggregated data only. Student identities are excluded."])
    writer.writerow([])
    writer.writerow(["Department summary"])
    writer.writerow(["Metric", "Value"])
    for key, value in data["counts"].items():
        writer.writerow([key.replace("_", " ").title(), value])
    writer.writerow(["Department average rating", data["counts"].get("average_rating", 0)])
    writer.writerow(["Feedback submission coverage %", data["submission_rate"]])
    writer.writerow([])
    writer.writerow(["Faculty performance"])
    writer.writerow(["Faculty", "Offerings", "Responses", "Average"])
    for row in data["faculty_performance"]:
        writer.writerow([row["name"], row["offering_count"], row["response_count"], row["average_rating"]])
    writer.writerow([])
    writer.writerow(["Semester analytics"])
    writer.writerow(["Semester", "Responses", "Average"])
    for row in data["semester_analytics"]:
        writer.writerow([row["semester_number"], row["response_count"], row["average_rating"]])
    writer.writerow([])
    writer.writerow(["Academic year comparison"])
    writer.writerow(["Academic year", "Responses", "Average"])
    for row in data["academic_year_comparison"]:
        writer.writerow([row["academic_year"], row["response_count"], row["average_rating"]])
    writer.writerow([])
    writer.writerow(["Most frequent improvement areas"])
    for row in data["improvement_areas"]:
        writer.writerow([row["title"], row["evidence"]])
    writer.writerow([])
    writer.writerow(["Sentiment summary"])
    for key, value in data["sentiment"]["summary"].items():
        writer.writerow([key, value])
    writer.writerow([])
    writer.writerow(["Topics"])
    writer.writerow(["Topic", "Mentions", "Positive", "Neutral", "Negative"])
    for row in data["sentiment"]["topics"]:
        writer.writerow([row["topic"], row["mentions"], row["positive"], row["neutral"], row["negative"]])
    return output.getvalue().encode("utf-8")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallMuted", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#64748b"), leading=11))
    styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading2"], fontSize=13, textColor=colors.HexColor("#0f172a"), spaceBefore=10, spaceAfter=6))
    return styles


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(18 * mm, 12 * mm, "FacultyInsight AI - Turning Student Feedback into Better Teaching")
    canvas.drawRightString(192 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _table(rows: list[list[Any]], widths: list[float] | None = None) -> Table:
    table = Table([[Paragraph(_safe(cell), _styles()["SmallMuted"]) for cell in row] for row in rows], colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _faculty_pdf(data: dict[str, Any], faculty: dict[str, Any]) -> bytes:
    styles = _styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=20 * mm)
    story: list[Any] = [
        Paragraph("FacultyInsight AI", styles["Title"]),
        Paragraph("Faculty Performance Report", styles["Heading1"]),
        Paragraph(_safe(f"Faculty: {faculty.get('name', '')}"), styles["Normal"]),
        Paragraph(_safe(f"Filters: {_filter_text(data['filters'])}"), styles["SmallMuted"]),
        Paragraph("Anonymous feedback: no student names, USNs, emails or identifiers are included.", styles["SmallMuted"]),
        Spacer(1, 8),
    ]
    summary = Table(
        [
            ["Overall average", "Responses", "Subject areas"],
            [f"{data['overall']['average_rating']:.2f} / 5", str(data["overall"]["response_count"]), str(len(data["subject_summary"]))],
        ],
        colWidths=[58 * mm, 45 * mm, 65 * mm],
    )
    summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ccfbf1")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#99f6e4")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([summary, Paragraph("Question-wise ratings", styles["SectionTitle"])])
    story.append(_table([["Question", "Average", "Ratings"]] + [[r["question_text"], f"{r['average_rating']:.2f}", r["response_count"]] for r in data["question_stats"]], [112, 28, 28]))
    story.append(Paragraph("Evidence-based strengths", styles["SectionTitle"]))
    if data["strengths"]:
        for item in data["strengths"]:
            story.append(Paragraph(_safe(f"<b>{item['title']}</b> - {item['evidence']}"), styles["SmallMuted"]))
    else:
        story.append(Paragraph("No strength reached the reporting threshold (3+ responses and 4.0+ average).", styles["SmallMuted"]))
    story.append(Paragraph("Evidence-based improvement areas", styles["SectionTitle"]))
    if data["improvement_areas"]:
        for item in data["improvement_areas"]:
            story.append(Paragraph(_safe(f"<b>{item['title']}</b> - {item['evidence']}"), styles["SmallMuted"]))
    else:
        story.append(Paragraph("No improvement area reached the reporting threshold (3+ responses and 3.0 or lower average).", styles["SmallMuted"]))
    story.append(Paragraph("Academic-year trend", styles["SectionTitle"]))
    story.append(_table([["Academic year", "Average", "Responses"]] + [[r["academic_year"], f"{r['average_rating']:.2f}", r["response_count"]] for r in data["trend"]], [58, 45, 45]))
    story.append(PageBreak())
    story.append(Paragraph("Anonymous student comments", styles["SectionTitle"]))
    story.append(Paragraph("Sentiment is produced by an explainable baseline unless a validated trained model is installed. Confidence is heuristic.", styles["SmallMuted"]))
    for row in data["comments"][:40]:
        story.append(Paragraph(_safe(f"<b>{row['subject_code']} ({row['academic_year']}) - {row['sentiment']['label']}</b>"), styles["SmallMuted"]))
        story.append(Paragraph(_safe(row["comment"]), styles["Normal"]))
        story.append(Spacer(1, 5))
    story.append(Paragraph("NLP limitations", styles["SectionTitle"]))
    story.append(Paragraph(_safe(data["sentiment"]["summary"]["limitations"]), styles["SmallMuted"]))
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


def _admin_pdf(data: dict[str, Any], filters: dict[str, Any]) -> bytes:
    styles = _styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=20 * mm)
    counts = data["counts"]
    story: list[Any] = [
        Paragraph("FacultyInsight AI", styles["Title"]),
        Paragraph("Department Analytics Report", styles["Heading1"]),
        Paragraph(_safe(f"Filters: {_filter_text(filters)}"), styles["SmallMuted"]),
        Paragraph("Aggregated data only. Student identities are excluded.", styles["SmallMuted"]),
        Spacer(1, 8),
    ]
    story.append(_table([
        ["Students", "Faculty", "Subjects", "Offerings", "Feedback"],
        [counts.get("total_students", 0), counts.get("total_faculty", 0), counts.get("total_subjects", 0), counts.get("offering_count", 0), counts.get("feedback_count", 0)],
    ], [34, 34, 34, 34, 34]))
    story.append(Paragraph(_safe(f"Department average rating: {counts.get('average_rating', 0):.2f}/5. Submission coverage: {data['submission_rate']}%."), styles["Normal"]))
    story.append(Paragraph("Faculty performance", styles["SectionTitle"]))
    story.append(_table([["Faculty", "Offerings", "Responses", "Average"]] + [[r["name"], r["offering_count"], r["response_count"], f"{r['average_rating']:.2f}"] for r in data["faculty_performance"]], [82, 25, 28, 28]))
    story.append(Paragraph("Semester analytics", styles["SectionTitle"]))
    story.append(_table([["Semester", "Responses", "Average"]] + [[r["semester_number"], r["response_count"], f"{r['average_rating']:.2f}"] for r in data["semester_analytics"]], [50, 40, 40]))
    story.append(Paragraph("Academic-year comparison", styles["SectionTitle"]))
    story.append(_table([["Academic year", "Responses", "Average"]] + [[r["academic_year"], r["response_count"], f"{r['average_rating']:.2f}"] for r in data["academic_year_comparison"]], [54, 38, 38]))
    story.append(Paragraph("Improvement areas with evidence", styles["SectionTitle"]))
    if data["improvement_areas"]:
        story.append(_table([["Area", "Evidence"]] + [[r["title"], r["evidence"]] for r in data["improvement_areas"]], [78, 85]))
    else:
        story.append(Paragraph("No improvement area reached the reporting threshold.", styles["SmallMuted"]))
    story.append(Paragraph("Sentiment overview", styles["SectionTitle"]))
    summary = data["sentiment"]["summary"]
    story.append(_table([["Positive", "Neutral", "Negative", "Method"], [summary["positive"], summary["neutral"], summary["negative"], summary["method"]]], [35, 35, 35, 55]))
    story.append(Paragraph(_safe(summary["limitations"]), styles["SmallMuted"]))
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
