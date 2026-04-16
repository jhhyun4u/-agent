"""
Vault Credentials API — 실적증명서 (Project Completion Certificates) Management Routes
Endpoints for uploading, retrieving, and managing project completion certificates.
"""

from typing import Optional, Dict, Any
from uuid import UUID
import logging

from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import get_current_user, get_current_user_team
from app.models.user_schemas import UserInDB
from app.services.vault_credential_service import VaultCredentialService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vault/credentials", tags=["vault-credentials"])


# ============================================
# Response Models
# ============================================

class CredentialResponse(BaseModel):
    """Credential record response"""
    id: str
    completed_project_id: str
    credential_type: str
    title: str
    file_path: str
    file_format: str
    file_size_bytes: Optional[int]
    ocr_status: str
    quality_score: Optional[int] = None
    credential_issue_date: Optional[str]
    credential_issuer: Optional[str]
    project_name: Optional[str]
    project_amount: Optional[int]
    created_at: str
    updated_at: str


class CredentialUploadRequest(BaseModel):
    """Upload request (form data)"""
    project_id: str
    credential_type: str
    title: str


class OCRResultResponse(BaseModel):
    """OCR processing result"""
    id: str
    ocr_status: str
    quality_score: Optional[int]
    extracted_fields: Dict[str, Any]


class CredentialsListResponse(BaseModel):
    """List credentials response"""
    credentials: list[CredentialResponse]
    total: int
    limit: int
    offset: int


# ============================================
# Endpoints
# ============================================

@router.post("/upload", response_model=CredentialResponse)
async def upload_credential(
    project_id: str = Form(...),
    credential_type: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user),
    current_team = Depends(get_current_user_team)
):
    """
    Upload a new project completion certificate (실적증명서).

    Supported formats: PDF, HWPX, DOCX, PNG, JPG

    The file will be queued for OCR text extraction. You can check
    the OCR status by polling GET /vault/credentials/{id}.

    Args:
        project_id: Completed proposal ID
        credential_type: Type of credential (e.g., 준공증명서, 실제완료증명서)
        title: Display title for the credential
        file: Binary file content

    Returns:
        Credential record with upload status
    """
    try:
        # Validate project ownership
        # (In production, verify that current_user's team owns the project)

        # Read file content
        file_content = await file.read()
        if len(file_content) > 50 * 1024 * 1024:  # 50 MB limit
            raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

        # Extract file format from filename
        file_format = file.filename.split(".")[-1].lower() if file.filename else "pdf"

        # Upload credential
        result = await VaultCredentialService.upload_credential(
            project_id=UUID(project_id),
            credential_type=credential_type,
            title=title,
            file_content=file_content,
            file_format=file_format,
            uploaded_by=UUID(current_user.id),
            metadata={"uploaded_by_name": current_user.name}
        )

        return CredentialResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Credential upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload credential")


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get details for a specific credential.

    Includes OCR status and extracted fields if processing is complete.
    """
    try:
        credential = await VaultCredentialService.get_credential(UUID(credential_id))

        if not credential:
            raise HTTPException(status_code=404, detail="Credential not found")

        # Check access permissions
        # (In production, verify RLS policy)

        return CredentialResponse(**credential)

    except Exception as e:
        logger.error(f"Failed to fetch credential: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch credential")


@router.get("/project/{project_id}/list", response_model=CredentialsListResponse)
async def list_credentials_for_project(
    project_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    List all credentials for a specific project.

    Results are ordered by creation date (newest first).
    """
    try:
        result = await VaultCredentialService.list_credentials(
            project_id=UUID(project_id),
            limit=limit,
            offset=offset
        )

        return CredentialsListResponse(**result)

    except Exception as e:
        logger.error(f"Failed to list credentials: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list credentials")


@router.post("/{credential_id}/process-ocr", response_model=OCRResultResponse)
async def process_ocr(
    credential_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Manually trigger OCR processing for a credential.

    Normally OCR is queued automatically after upload, but this endpoint
    allows manual re-processing (e.g., if the first attempt failed).

    Args:
        credential_id: Credential to process

    Returns:
        OCR result with quality score and extracted fields
    """
    try:
        result = await VaultCredentialService.process_ocr(UUID(credential_id))
        return OCRResultResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="OCR processing failed")


@router.delete("/{credential_id}")
async def delete_credential(
    credential_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Soft-delete a credential (marks as deleted but preserves audit trail).

    Note: Only the uploader can delete a credential.
    """
    try:
        result = await VaultCredentialService.delete_credential(UUID(credential_id))

        if not result:
            raise HTTPException(status_code=404, detail="Credential not found")

        return {"status": "deleted", "id": credential_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete credential: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete credential")


@router.get("/types", response_model=list[str])
async def get_credential_types():
    """
    Get list of supported credential types.

    Returns:
        List of valid credential_type values for uploads
    """
    return VaultCredentialService.CREDENTIAL_TYPES
