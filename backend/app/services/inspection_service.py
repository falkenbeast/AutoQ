import csv
from datetime import datetime, timezone
import io
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from fastapi import UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.exceptions import (
    EntityNotFoundException,
    InvalidCSVException,
    ValidationException,
)
from app.models.component import Component
from app.models.inspection import Inspection
from app.schemas.inspection import (
    CSVUploadResponse,
    InspectionCreate,
    InspectionResponse,
    InspectionUpdate,
)
from app.services.component_service import component_service

logger = logging.getLogger("autoq.services.inspection")


class InspectionService:
    """Service layer managing database-backed automotive quality inspection operations."""

    REQUIRED_CSV_COLUMNS = [
        "component_id",
        "component_name",
        "component_category",
        "manufacturing_temperature",
        "pressure",
        "production_batch",
        "inspection_result",
    ]

    def get_inspections(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        category: Optional[str] = None,
        batch: Optional[str] = None,
        component_id: Optional[str] = None,
    ) -> Tuple[List[Inspection], int]:
        """Queries paginated inspection records with multi-attribute filtering."""
        query = db.query(Inspection).join(Inspection.component)

        if status:
            clean_status = status.strip().capitalize()
            query = query.filter(Inspection.inspection_result == clean_status)
        if category:
            query = query.filter(
                func.lower(Component.component_category) == category.strip().lower()
            )
        if batch:
            query = query.filter(
                func.lower(Inspection.production_batch) == batch.strip().lower()
            )
        if component_id:
            query = query.filter(
                func.lower(Inspection.component_id) == component_id.strip().lower()
            )

        total = query.count()
        items = (
            query.order_by(Inspection.inspection_date.desc(), Inspection.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    def get_inspection_by_id(
        self,
        db: Session,
        inspection_id: Union[int, str],
    ) -> Inspection:
        """Retrieves a single inspection record by primary key."""
        try:
            int_id = int(str(inspection_id).replace("AQ-", "").strip())
        except ValueError:
            raise EntityNotFoundException("Inspection", inspection_id)

        inspection = db.query(Inspection).filter(Inspection.id == int_id).first()
        if not inspection:
            raise EntityNotFoundException("Inspection", inspection_id)
        return inspection

    def create_inspection(
        self,
        db: Session,
        payload: InspectionCreate,
    ) -> Inspection:
        """Validates, links or creates component, and persists an inspection record."""
        # Ensure component exists or auto-catalog it
        component_service.get_or_create_component(
            db,
            component_id=payload.component_id,
            component_name=payload.component_name,
            component_category=payload.component_category,
        )

        inspection = Inspection(
            component_id=payload.component_id,
            manufacturing_temperature=payload.manufacturing_temperature,
            pressure=payload.pressure,
            production_batch=payload.production_batch,
            inspection_date=payload.inspection_date,
            inspection_result=payload.inspection_result.value if hasattr(payload.inspection_result, "value") else str(payload.inspection_result),
            defect_category=payload.defect_category,
            notes=payload.notes,
        )
        db.add(inspection)
        db.commit()
        db.refresh(inspection)
        logger.info(f"Persisted inspection record: id={inspection.id} component={inspection.component_id}")
        return inspection

    def update_inspection(
        self,
        db: Session,
        inspection_id: Union[int, str],
        payload: InspectionUpdate,
    ) -> Inspection:
        """Updates parameters or notes of an existing inspection record."""
        inspection = self.get_inspection_by_id(db, inspection_id)
        update_data = payload.model_dump(exclude_unset=True)

        # If component metadata changed, update component
        if "component_name" in update_data or "component_category" in update_data:
            comp = inspection.component
            if comp:
                if update_data.get("component_name"):
                    comp.component_name = update_data.pop("component_name")
                if update_data.get("component_category"):
                    comp.component_category = update_data.pop("component_category")
                db.flush()

        # Update remaining inspection fields
        for key, val in update_data.items():
            if val is not None:
                if key == "inspection_result" and hasattr(val, "value"):
                    val = val.value
                setattr(inspection, key, val)

        db.commit()
        db.refresh(inspection)
        logger.info(f"Updated inspection record: id={inspection.id}")
        return inspection

    def delete_inspection(
        self,
        db: Session,
        inspection_id: Union[int, str],
    ) -> Dict[str, Any]:
        """Deletes an inspection record by primary key, decoupling linked predictions safely."""
        inspection = self.get_inspection_by_id(db, inspection_id)
        del_id = inspection.id
        from app.models.prediction import Prediction
        db.query(Prediction).filter(Prediction.inspection_id == del_id).update(
            {Prediction.inspection_id: None}, synchronize_session="fetch"
        )
        db.delete(inspection)
        db.commit()
        logger.info(f"Deleted inspection record: id={del_id} and decoupled linked predictions")
        return {
            "status": "success",
            "message": f"Inspection record '{del_id}' deleted successfully.",
            "deleted_id": del_id,
        }

    async def process_csv_upload(
        self,
        db: Session,
        file: UploadFile,
    ) -> CSVUploadResponse:
        """
        Parses and imports bulk inspection CSV data with transaction handling,
        validation, deduplication, and detailed row-by-row error tracking.
        """
        if not file.filename.lower().endswith(".csv"):
            raise InvalidCSVException("Uploaded file must have a .csv extension.")

        content = await file.read()
        file_size = len(content)

        MAX_CSV_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
        if file_size > MAX_CSV_SIZE_BYTES:
            raise InvalidCSVException(
                f"CSV file size ({file_size / (1024*1024):.1f} MB) exceeds maximum allowed limit of 10 MB."
            )

        if file_size == 0:
            raise InvalidCSVException("The uploaded CSV file is empty (0 bytes).")

        try:
            text_content = content.decode("utf-8-sig")
            csv_reader = csv.DictReader(io.StringIO(text_content))

            if not csv_reader.fieldnames:
                raise InvalidCSVException("CSV file contains no readable header line.")

            # Validate header schema
            header_map = {col.strip().lower(): col for col in csv_reader.fieldnames}
            missing_cols = [
                req for req in self.REQUIRED_CSV_COLUMNS if req not in header_map
            ]

            if missing_cols:
                raise InvalidCSVException(
                    f"CSV missing required columns: {', '.join(missing_cols)}",
                    errors=[f"Missing column: {c}" for c in missing_cols],
                )

            preview_rows: List[Dict[str, Any]] = []
            errors: List[str] = []
            imported_count = 0
            rejected_count = 0

            for idx, raw_row in enumerate(csv_reader, start=1):
                clean_row = {
                    col.strip().lower(): val.strip() for col, val in raw_row.items() if col
                }

                cid = clean_row.get("component_id", "").strip().upper()
                cname = clean_row.get("component_name", "").strip()
                ccat = clean_row.get("component_category", "").strip()
                temp_str = clean_row.get("manufacturing_temperature", "")
                press_str = clean_row.get("pressure", "")
                batch = clean_row.get("production_batch", "").strip().upper()
                res_str = clean_row.get("inspection_result", "").strip().capitalize()
                defect_cat = clean_row.get("defect_category", "").strip() or None
                notes_str = clean_row.get("notes", "").strip() or None
                date_str = clean_row.get("inspection_date", "").strip()

                # Row Validation
                row_errs = []
                if not cid or len(cid) < 3:
                    row_errs.append("Invalid or missing component_id")
                if not cname:
                    cname = f"Component {cid}"
                if not ccat:
                    ccat = "General Mechanical"

                try:
                    temp_val = float(temp_str)
                    if temp_val <= 0 or temp_val > 2500:
                        row_errs.append("Temperature must be between 0 and 2500°C")
                except ValueError:
                    row_errs.append(f"Invalid numeric temperature: '{temp_str}'")
                    temp_val = 0.0

                try:
                    press_val = float(press_str)
                    if press_val <= 0 or press_val > 1000:
                        row_errs.append("Pressure must be between 0 and 1000 bar")
                except ValueError:
                    row_errs.append(f"Invalid numeric pressure: '{press_str}'")
                    press_val = 0.0

                if not batch:
                    row_errs.append("Missing production_batch")

                if res_str not in ["Passed", "Defective"]:
                    row_errs.append(f"Result '{res_str}' must be 'Passed' or 'Defective'")

                # Parse date
                insp_date = datetime.now(timezone.utc)
                if date_str:
                    try:
                        insp_date = datetime.fromisoformat(date_str)
                    except ValueError:
                        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                            try:
                                insp_date = datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                                break
                            except ValueError:
                                pass

                if row_errs:
                    rejected_count += 1
                    errors.append(f"Row {idx} ({cid}): {'; '.join(row_errs)}")
                    continue

                # Deduplication check: check if inspection with exact cid, batch, and date exists
                existing = db.query(Inspection).filter(
                    Inspection.component_id == cid,
                    Inspection.production_batch == batch,
                    Inspection.inspection_date == insp_date,
                ).first()

                if existing:
                    rejected_count += 1
                    errors.append(f"Row {idx} ({cid}): Duplicate inspection record already exists for batch {batch}")
                    continue

                # Ensure component exists
                component_service.get_or_create_component(
                    db,
                    component_id=cid,
                    component_name=cname,
                    component_category=ccat,
                )

                # Create inspection
                inspection = Inspection(
                    component_id=cid,
                    manufacturing_temperature=temp_val,
                    pressure=press_val,
                    production_batch=batch,
                    inspection_date=insp_date,
                    inspection_result=res_str,
                    defect_category=defect_cat if res_str == "Defective" else None,
                    notes=notes_str,
                )
                db.add(inspection)
                imported_count += 1

                if len(preview_rows) < 10:
                    preview_rows.append({
                        "component_id": cid,
                        "component_name": cname,
                        "category": ccat,
                        "temperature": temp_val,
                        "pressure": press_val,
                        "batch": batch,
                        "result": res_str,
                        "defect_category": defect_cat or "None",
                    })

            # Commit batch
            if imported_count > 0:
                db.commit()
                logger.info(f"Imported {imported_count} inspections from CSV ({rejected_count} rejected)")
            else:
                db.rollback()

            total_evaluated = imported_count + rejected_count

            return CSVUploadResponse(
                filename=file.filename,
                file_size_bytes=file_size,
                total_rows=total_evaluated,
                valid_rows=imported_count,
                imported_rows=imported_count,
                rejected_rows=rejected_count,
                errors=errors[:15],
                preview=preview_rows,
                status="COMPLETED" if imported_count > 0 else "FAILED",
                message=(
                    f"CSV batch import completed: {imported_count} imported, "
                    f"{rejected_count} rejected."
                ),
            )

        except UnicodeDecodeError:
            raise InvalidCSVException("Failed to decode CSV file. File must be UTF-8 encoded.")
        except InvalidCSVException:
            raise
        except Exception as exc:
            db.rollback()
            logger.error(f"Error during CSV batch processing: {exc}", exc_info=True)
            raise InvalidCSVException(f"Error processing CSV file: {str(exc)}")


inspection_service = InspectionService()
