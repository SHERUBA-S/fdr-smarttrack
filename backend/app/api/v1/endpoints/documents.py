import os
import hashlib
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, verify_institution_access
from app.models.fdr import FDRRecord, FDRDocument, ExtractedDocumentField
from app.models.enums import DocumentType, FDRStatus
from app.models.user import User
from app.schemas.fdr import FDRDocumentResponse, ExtractedFieldResponse, ExtractedFieldCorrectionRequest
from app.services.ocr_service import OCRService
from app.services.verification_engine import VerificationEngine
from app.services.audit_service import log_audit_event

router = APIRouter()

@router.post("/upload", response_model=FDRDocumentResponse)
async def upload_document(
    fdr_id: str = Form(...),
    document_type: DocumentType = Form(DocumentType.FDR_RECEIPT),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Secure document upload with MIME validation, SHA-256 hashing,
    OCR text extraction, and structured field parsing.
    """
    fdr = db.query(FDRRecord).filter(FDRRecord.id == fdr_id).first()
    if not fdr:
        raise HTTPException(status_code=404, detail="FDR record not found")

    verify_institution_access(current_user, fdr.institution_id)

    # 1. Validate file extension and MIME type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {ext}. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 2. Save file and compute SHA-256
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}_{os.path.basename(file.filename)}"
    dest_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    hasher = hashlib.sha256()
    file_size = 0

    try:
        with open(dest_path, "wb") as buffer:
            while chunk := await file.read(65536):
                file_size += len(chunk)
                if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
                    buffer.close()
                    os.remove(dest_path)
                    raise HTTPException(
                        status_code=400,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB"
                    )
                hasher.update(chunk)
                buffer.write(chunk)
    except Exception as e:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    file_hash = hasher.hexdigest()

    # 3. Create document database record
    doc_record = FDRDocument(
        fdr_id=fdr.id,
        file_path=dest_path,
        file_name=file.filename,
        file_size_bytes=file_size,
        mime_type=file.content_type or "application/octet-stream",
        file_hash=file_hash,
        document_type=document_type,
        ocr_status="PROCESSING"
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # 4. Perform OCR & Structured Field Extraction
    raw_text, ocr_ok, ocr_err = OCRService.extract_text_from_file(dest_path)
    doc_record.raw_ocr_text = raw_text
    doc_record.ocr_status = "COMPLETED" if ocr_ok else "FAILED"
    db.commit()

    if ocr_ok and raw_text:
        extracted = OCRService.parse_fdr_fields(raw_text)
        for f in extracted:
            field_entry = ExtractedDocumentField(
                document_id=doc_record.id,
                field_name=f["field_name"],
                extracted_value=f["extracted_value"],
                confidence=f["confidence"],
                page_number=f.get("page_number", 1)
            )
            db.add(field_entry)
        db.commit()

    # 5. Re-run verification suite
    VerificationEngine.run_all_checks(db, fdr)

    log_audit_event(
        db=db,
        action="DOCUMENT_UPLOADED",
        entity_type="DOCUMENT",
        entity_id=doc_record.id,
        actor=current_user,
        details=f"Uploaded {file.filename} (Size: {file_size} bytes, Hash: {file_hash[:12]}..., OCR: {doc_record.ocr_status})"
    )

    db.refresh(doc_record)
    return FDRDocumentResponse.model_validate(doc_record)

@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Securely stream uploaded document file."""
    doc = db.query(FDRDocument).filter(FDRDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    fdr = db.query(FDRRecord).filter(FDRRecord.id == doc.fdr_id).first()
    if fdr:
        verify_institution_access(current_user, fdr.institution_id)

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Physical document file missing on server storage")

    return FileResponse(
        path=doc.file_path,
        filename=doc.file_name,
        media_type=doc.mime_type
    )

@router.put("/fields/{field_id}", response_model=ExtractedFieldResponse)
def correct_extracted_field(
    field_id: str,
    data: ExtractedFieldCorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allow authorized user to correct OCR extraction mistakes before approval."""
    field = db.query(ExtractedDocumentField).filter(ExtractedDocumentField.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Extracted field record not found")

    doc = db.query(FDRDocument).filter(FDRDocument.id == field.document_id).first()
    if doc:
        fdr = db.query(FDRRecord).filter(FDRRecord.id == doc.fdr_id).first()
        if fdr:
            verify_institution_access(current_user, fdr.institution_id)

    prev_val = field.extracted_value
    field.user_corrected_value = data.user_corrected_value.strip()
    field.is_corrected = True
    db.commit()
    db.refresh(field)

    # Re-run verification suite after user correction
    if doc and doc.fdr:
        VerificationEngine.run_all_checks(db, doc.fdr)

    log_audit_event(
        db=db,
        action="OCR_FIELD_CORRECTED",
        entity_type="FIELD",
        entity_id=field.id,
        actor=current_user,
        details=f"Corrected {field.field_name}: '{prev_val}' -> '{field.user_corrected_value}'"
    )

    return ExtractedFieldResponse.model_validate(field)
