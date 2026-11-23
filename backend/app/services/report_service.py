"""
AutoQ - Quality Audit Report Management & Rendering Service
Generates genuine CSV and PDF inspection audit documents from SQLite database records,
catalogs file metadata in the reports table, and serves secure downloads.
"""
from datetime import datetime, timezone, timedelta
import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple, Union
import pandas as pd
from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import EntityNotFoundException, ValidationException
from app.models.component import Component
from app.models.inspection import Inspection
from app.models.prediction import Prediction
from app.models.report import Report
from app.schemas.report import ReportFormatEnum, ReportGenerateRequest

# ReportLab PDF imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logger = logging.getLogger("autoq.services.report")


class ReportService:
    """
    Service responsible for quality audit report generation and file lifecycle.
    Stores report metadata in SQLite and renders physical documents into backend/reports/.
    """

    def __init__(self):
        self.report_dir = Path(settings.REPORT_STORAGE_PATH).resolve()
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        db: Session,
        payload: ReportGenerateRequest,
    ) -> Report:
        """
        Creates report metadata record and immediately renders the physical CSV or PDF document.
        Guarantees that generated reports contain actual database telemetry.
        """
        raw_batch = payload.target_batch or payload.batch
        has_batch_filter = bool(raw_batch and raw_batch.upper() != "ALL")
        batch_label = raw_batch.strip() if has_batch_filter else "All-Batches"
        report_name = f"{payload.report_type.value} – {batch_label}"
        ext = payload.format.value.lower()

        # 1. Query actual inspection data
        query = db.query(Inspection)
        if has_batch_filter:
            query = query.filter(func.lower(Inspection.production_batch) == batch_label.lower())

        # Date range filtering
        now = datetime.now(timezone.utc)
        if payload.date_range:
            dr = payload.date_range.strip().lower()
            if "7" in dr:
                cutoff = now - timedelta(days=7)
                query = query.filter(Inspection.inspection_date >= cutoff)
            elif "14" in dr:
                cutoff = now - timedelta(days=14)
                query = query.filter(Inspection.inspection_date >= cutoff)
            elif "30" in dr:
                cutoff = now - timedelta(days=30)
                query = query.filter(Inspection.inspection_date >= cutoff)
            elif "month" in dr:
                cutoff = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
                query = query.filter(Inspection.inspection_date >= cutoff)

        inspections = query.order_by(Inspection.inspection_date.desc()).limit(1000).all()

        if not inspections:
            raise ValidationException(
                f"No qualifying inspection records found in SQLite for batch '{batch_label}' "
                f"within {payload.date_range or 'selected audit period'}. Please adjust filters or ingest inspection data."
            )

        predictions = db.query(Prediction).order_by(Prediction.created_at.desc()).limit(200).all()

        # 2. Initialize Report in database
        report = Report(
            report_name=report_name,
            report_type=payload.report_type.value,
            report_status="GENERATING",
            description=payload.description or f"Quality audit report for batch {batch_label} ({payload.date_range}).",
            generated_at=datetime.now(timezone.utc),
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_batch = batch_label.replace(" ", "_")
        file_name = f"REP-{report.id:04d}-{safe_batch}-{timestamp_str}.{ext}"
        target_path = self.report_dir / file_name
        report.file_path = str(target_path)

        total = len(inspections)
        passed = sum(1 for i in inspections if i.inspection_result == "Passed")
        defective = sum(1 for i in inspections if i.inspection_result == "Defective")
        defect_rate = round((defective / total) * 100, 2) if total > 0 else 0.0

        # Defect categories breakdown
        defect_cat_counts = {}
        for i in inspections:
            if i.inspection_result == "Defective" and i.defect_category:
                defect_cat_counts[i.defect_category] = defect_cat_counts.get(i.defect_category, 0) + 1

        # 3. Render physical document
        try:
            if payload.format == ReportFormatEnum.CSV:
                self._render_csv(
                    target_path=target_path,
                    report=report,
                    batch_label=batch_label,
                    total=total,
                    passed=passed,
                    defective=defective,
                    defect_rate=defect_rate,
                    defect_cat_counts=defect_cat_counts,
                    inspections=inspections,
                )
            else:
                self._render_pdf(
                    target_path=target_path,
                    report=report,
                    batch_label=batch_label,
                    total=total,
                    passed=passed,
                    defective=defective,
                    defect_rate=defect_rate,
                    defect_cat_counts=defect_cat_counts,
                    inspections=inspections,
                    predictions=predictions,
                )

            report.report_status = "COMPLETED"
            db.commit()
            db.refresh(report)
            logger.info(f"Successfully rendered {ext.upper()} report: id={report.id} path='{target_path}'")
        except Exception as exc:
            report.report_status = "FAILED"
            db.commit()
            logger.error(f"Failed to render report id={report.id}: {exc}", exc_info=True)
            raise exc

        return report

    def _render_csv(
        self,
        target_path: Path,
        report: Report,
        batch_label: str,
        total: int,
        passed: int,
        defective: int,
        defect_rate: float,
        defect_cat_counts: dict,
        inspections: List[Inspection],
    ):
        """Writes structured quality audit CSV report with executive summary and telemetry rows."""
        lines = [
            f"# AutoQ Automotive Quality Intelligence System – Inspection Audit Report",
            f"# Report ID: REP-{report.id:04d}",
            f"# Report Title: {report.report_name}",
            f"# Production Batch: {batch_label}",
            f"# Generated Timestamp (UTC): {report.generated_at.isoformat()}",
            f"# Total Inspected Units: {total}",
            f"# Conforming Units (Passed): {passed}",
            f"# Non-Conforming Units (Defective): {defective}",
            f"# First-Pass Defect Rate: {defect_rate}%",
            f"#",
            f"# DEFECT TAXONOMY BREAKDOWN",
        ]
        for cat, cnt in defect_cat_counts.items():
            lines.append(f"# Defect Category: {cat} = {cnt} ({cnt/defective*100:.1f}%)" if defective > 0 else f"# Defect Category: {cat} = {cnt}")

        lines.append("#" + "=" * 70)
        lines.append("Inspection_ID,Component_ID,Component_Name,Category,Batch,Temperature_C,Pressure_bar,Inspection_Date,Result,Defect_Category,Notes")

        for insp in inspections:
            c_name = f'"{insp.component_name}"' if insp.component_name else '""'
            c_cat = f'"{insp.component_category}"' if insp.component_category else '""'
            d_cat = f'"{insp.defect_category}"' if insp.defect_category else '""'
            notes = f'"{insp.notes}"' if insp.notes else '""'
            lines.append(
                f"{insp.id},{insp.component_id},{c_name},{c_cat},{insp.production_batch},"
                f"{insp.manufacturing_temperature},{insp.pressure},{insp.inspection_date.strftime('%Y-%m-%d %H:%M:%S')},"
                f"{insp.inspection_result},{d_cat},{notes}"
            )

        with open(target_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def _render_pdf(
        self,
        target_path: Path,
        report: Report,
        batch_label: str,
        total: int,
        passed: int,
        defective: int,
        defect_rate: float,
        defect_cat_counts: dict,
        inspections: List[Inspection],
        predictions: List[Prediction],
    ):
        """Renders professional multi-page quality audit report PDF with ReportLab."""
        doc = SimpleDocTemplate(
            str(target_path),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Title"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0F172A"),
            alignment=0,
            spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
            spaceAfter=12,
        )
        heading_style = ParagraphStyle(
            "DocHeading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#1E293B"),
            spaceBefore=10,
            spaceAfter=6,
        )
        cell_style = ParagraphStyle(
            "DocCell",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1E293B"),
        )
        cell_bold = ParagraphStyle(
            "DocCellBold",
            parent=cell_style,
            fontName="Helvetica-Bold",
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph("<b>AutoQ</b> – Automotive Quality Intelligence System", title_style))
        story.append(
            Paragraph(
                f"Official Quality Engineering Audit Report &bull; Reference: <b>REP-{report.id:04d}</b> &bull; Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                subtitle_style,
            )
        )
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=10))

        # 2. Audit Metadata Block
        meta_data = [
            [
                Paragraph("<b>Report Name:</b>", cell_style),
                Paragraph(report.report_name, cell_style),
                Paragraph("<b>Production Batch:</b>", cell_style),
                Paragraph(batch_label, cell_bold),
            ],
            [
                Paragraph("<b>Audit Type:</b>", cell_style),
                Paragraph(report.report_type, cell_style),
                Paragraph("<b>Target Yield:</b>", cell_style),
                Paragraph("90.0% Minimum", cell_style),
            ],
        ]
        meta_table = Table(meta_data, colWidths=[90, 180, 95, 175])
        meta_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        story.append(meta_table)
        story.append(Spacer(1, 12))

        # 3. Executive KPI Summary Table
        story.append(Paragraph("Executive Quality Summary", heading_style))
        kpi_data = [
            ["Metric Parameter", "Count / Value", "Standard Benchmark", "Compliance Status"],
            ["Total Inspected Parts", f"{total:,}", "Batch Quota", "Verified 100%"],
            ["Conforming Parts (Passed)", f"{passed:,}", "≥ 90.0%", "Conforming"],
            ["Non-Conforming Parts (Defects)", f"{defective:,}", "≤ 10.0%", "Critical Action" if defect_rate > 10 else "Acceptable"],
            ["First-Pass Defect Rate", f"{defect_rate}%", "≤ 10.0%", "DEFICIT" if defect_rate > 10 else "NOMINAL"],
        ]
        kpi_table = Table(kpi_data, colWidths=[180, 110, 120, 130])
        kpi_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
            ])
        )
        story.append(kpi_table)
        story.append(Spacer(1, 12))

        # 4. Defect Taxonomy Breakdown
        if defect_cat_counts:
            story.append(Paragraph("Defect Taxonomy Breakdown (Root Causes)", heading_style))
            defect_rows = [["Defect Category", "Detected Instances", "Proportion of Total Defects"]]
            for cat, count in defect_cat_counts.items():
                pct = round((count / defective) * 100, 1) if defective > 0 else 0.0
                defect_rows.append([cat, str(count), f"{pct}%"])

            defect_table = Table(defect_rows, colWidths=[240, 150, 150])
            defect_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FEF2F2")]),
                    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                ])
            )
            story.append(defect_table)
            story.append(Spacer(1, 12))

        # 5. Recent Inspection Audit Telemetry (Sample up to 15 rows)
        story.append(Paragraph(f"Recent Physical Inspection Records (Sample of {min(15, total)} logged)", heading_style))
        sample_rows = [["ID", "Component ID", "Category", "Temp (°C)", "Press (bar)", "Result", "Defect Mode"]]
        for insp in inspections[:15]:
            sample_rows.append([
                str(insp.id),
                insp.component_id,
                insp.component_category or "Powertrain",
                f"{insp.manufacturing_temperature:.1f}",
                f"{insp.pressure:.1f}",
                insp.inspection_result,
                insp.defect_category or "None",
            ])

        sample_table = Table(sample_rows, colWidths=[35, 95, 110, 65, 65, 65, 105])
        sample_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("FONTSIZE", (0, 1), (-1, -1), 7),
                ("ALIGN", (3, 1), (5, -1), "CENTER"),
            ])
        )
        story.append(sample_table)

        # Build Document
        doc.build(story)

    def get_reports(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Report], int]:
        """Queries archived report metadata records from SQLite."""
        query = db.query(Report)
        total = query.count()
        items = query.order_by(Report.generated_at.desc(), Report.id.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_report_by_id(
        self,
        db: Session,
        report_id: Union[int, str],
    ) -> Report:
        """Retrieves a single report metadata record by ID."""
        try:
            int_id = int(str(report_id).replace("REP-", "").split("-")[0].strip())
        except ValueError:
            raise EntityNotFoundException("Report", report_id)

        rep = db.query(Report).filter(Report.id == int_id).first()
        if not rep:
            raise EntityNotFoundException("Report", report_id)
        return rep

    def get_report_file_for_download(
        self,
        db: Session,
        report_id: Union[int, str],
    ) -> Tuple[Path, str, str]:
        """
        Retrieves file path and content type for downloading.
        Guarantees path security against directory traversal attacks.
        """
        report = self.get_report_by_id(db=db, report_id=report_id)

        if not report.file_path:
            raise EntityNotFoundException("Report File", f"Report {report.id} has no generated file path.")

        file_path = Path(report.file_path).resolve()

        # If file is not found at exact recorded path (e.g. from previous directory structures),
        # look inside canonical self.report_dir by filename
        if not file_path.is_file():
            alt_path = (self.report_dir / file_path.name).resolve()
            if alt_path.is_file():
                file_path = alt_path

        # Strict security check against path traversal
        try:
            if not file_path.is_relative_to(self.report_dir):
                raise ValidationException("Security Error: Invalid report file location.")
        except AttributeError:
            if not str(file_path).startswith(str(self.report_dir)):
                raise ValidationException("Security Error: Invalid report file location.")

        if not file_path.is_file() or file_path.stat().st_size == 0:
            raise EntityNotFoundException("Report File", f"Physical report file '{file_path.name}' not found on server.")

        filename = file_path.name
        media_type = "application/pdf" if filename.endswith(".pdf") else "text/csv"
        return file_path, filename, media_type


report_service = ReportService()
