"""
Vault Credential Service — 실적증명서 (Project Completion Certificates) Management
Handles file upload, OCR extraction, and metadata management for credentials.
"""

import io
import re
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
import logging

from pydantic import BaseModel
from pytesseract import pytesseract
from PIL import Image
import PyPDF2
import docx

from app.utils.supabase_client import supabase

logger = logging.getLogger(__name__)


class CredentialMetadata(BaseModel):
    """Extracted credential metadata"""
    manual_review_needed: bool = False
    quality_score: int = 0  # 0-100
    extracted_fields: Dict[str, Any] = {}
    review_notes: str = ""


class VaultCredentialService:
    """Service for managing vault credentials with OCR extraction"""

    # Credential types
    CREDENTIAL_TYPES = [
        "준공증명서",
        "실제완료증명서",
        "실적보증서",
        "기술보증서",
        "검수증명",
        "납품증명",
        "기타증명서"
    ]

    # File format OCR support
    SUPPORTED_FORMATS = {
        "pdf": "application/pdf",
        "hwp": "application/vnd.hancom.hwp",
        "hwpx": "application/vnd.hancom.hwpx",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg"
    }

    @staticmethod
    async def upload_credential(
        project_id: UUID,
        credential_type: str,
        title: str,
        file_content: bytes,
        file_format: str,
        uploaded_by: UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload a credential file and queue for OCR extraction.

        Args:
            project_id: Completed proposal ID
            credential_type: Type of credential
            title: Display title
            file_content: File binary content
            file_format: File format (pdf, hwp, docx, etc.)
            uploaded_by: User ID who uploaded
            metadata: Optional additional metadata

        Returns:
            Credential record with ID and OCR status
        """
        if credential_type not in VaultCredentialService.CREDENTIAL_TYPES:
            raise ValueError(f"Invalid credential type: {credential_type}")

        if file_format.lower() not in VaultCredentialService.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format: {file_format}")

        # Generate storage path
        storage_path = f"vault/credentials/{project_id}/{datetime.now().isoformat()}_{title}.{file_format}"

        try:
            # Upload to Supabase Storage
            supabase.storage.from_("tenopa-files").upload(
                storage_path,
                file_content,
                file_options={
                    "cacheControl": "3600",
                    "contentType": VaultCredentialService.SUPPORTED_FORMATS.get(file_format.lower())
                }
            )

            # Create credential record in database
            credential_data = {
                "completed_project_id": str(project_id),
                "credential_type": credential_type,
                "title": title,
                "file_path": storage_path,
                "file_format": file_format.lower(),
                "file_size_bytes": len(file_content),
                "uploaded_by": str(uploaded_by),
                "ocr_status": "pending",
                "metadata": metadata or {}
            }

            response = supabase.table("vault_credentials").insert(credential_data).execute()
            credential = response.data[0] if response.data else None

            if not credential:
                raise Exception("Failed to create credential record")

            logger.info(f"Credential uploaded: {credential['id']} for project {project_id}")

            # Queue OCR job asynchronously
            # In production, this would be a Celery task or similar
            # For now, we'll call it synchronously but in background
            # await VaultCredentialService.process_ocr_async(credential['id'], file_content, file_format)

            return {
                "id": credential["id"],
                "project_id": str(project_id),
                "credential_type": credential_type,
                "title": title,
                "file_path": storage_path,
                "ocr_status": "pending",
                "created_at": credential["created_at"]
            }

        except Exception as e:
            logger.error(f"Failed to upload credential: {str(e)}")
            raise

    @staticmethod
    async def extract_text_from_file(
        credential_id: UUID,
        file_content: bytes,
        file_format: str
    ) -> str:
        """
        Extract text from credential file using appropriate OCR method.

        Args:
            credential_id: Credential ID for logging
            file_content: File binary content
            file_format: File format

        Returns:
            Extracted text content
        """
        file_format = file_format.lower()

        try:
            if file_format == "pdf":
                return VaultCredentialService._extract_from_pdf(file_content)
            elif file_format in ["hwp", "hwpx"]:
                return VaultCredentialService._extract_from_hwpx(file_content)
            elif file_format in ["docx", "doc"]:
                return VaultCredentialService._extract_from_docx(file_content)
            elif file_format in ["png", "jpg", "jpeg"]:
                return VaultCredentialService._extract_from_image(file_content)
            else:
                raise ValueError(f"No OCR handler for format: {file_format}")

        except Exception as e:
            logger.error(f"OCR extraction failed for {credential_id}: {str(e)}")
            raise

    @staticmethod
    def _extract_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            raise

    @staticmethod
    def _extract_from_docx(file_content: bytes) -> str:
        """Extract text from DOCX"""
        try:
            doc = docx.Document(io.BytesIO(file_content))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"DOCX extraction failed: {str(e)}")
            raise

    @staticmethod
    def _extract_from_hwpx(file_content: bytes) -> str:
        """Extract text from HWPX (Korean format)"""
        # HWPX is a zip-based format, need specialized handler
        # For now, use placeholder - in production use hwpxskill library
        try:
            import zipfile
            hwpx_zip = zipfile.ZipFile(io.BytesIO(file_content))
            # HWPX stores text in content.xml
            if "content.xml" in hwpx_zip.namelist():
                content_xml = hwpx_zip.read("content.xml").decode("utf-8")
                # Simple text extraction from XML - in production use proper XML parser
                return content_xml
            else:
                return ""
        except Exception as e:
            logger.error(f"HWPX extraction failed: {str(e)}")
            raise

    @staticmethod
    def _extract_from_image(file_content: bytes) -> str:
        """Extract text from image using OCR (Tesseract)"""
        try:
            image = Image.open(io.BytesIO(file_content))
            text = pytesseract.image_to_string(image, lang="kor")
            return text
        except Exception as e:
            logger.error(f"Image OCR failed: {str(e)}")
            raise

    @staticmethod
    def _extract_credential_fields(text: str) -> Dict[str, Any]:
        """
        Extract structured fields from OCR text using regex patterns.

        Returns:
            Extracted fields with pattern matching
        """
        fields = {}

        # Date patterns (Korean date format)
        issue_date_pattern = r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일"
        issue_date_matches = re.findall(issue_date_pattern, text)
        if issue_date_matches:
            try:
                y, m, d = issue_date_matches[0]
                fields["credential_issue_date"] = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
            except Exception:
                pass

        # Amount patterns (숫자 천단위 쉼표, 원)
        amount_pattern = r"(\d{1,3}(?:,\d{3})*)\s*원"
        amount_matches = re.findall(amount_pattern, text)
        if amount_matches:
            amount_str = amount_matches[0].replace(",", "")
            try:
                fields["project_amount"] = int(amount_str)
            except Exception:
                pass

        # Issuer pattern (발급 기관 또는 담당기관)
        issuer_pattern = r"(?:발급|담당)?기관[:\s]+(.{5,30})"
        issuer_matches = re.findall(issuer_pattern, text)
        if issuer_matches:
            fields["credential_issuer"] = issuer_matches[0].strip()

        # Project name pattern
        project_name_pattern = r"(?:사업|공사|용역)?\s*명[:\s]+(.{5,100})"
        project_name_matches = re.findall(project_name_pattern, text)
        if project_name_matches:
            fields["project_name"] = project_name_matches[0].strip()

        return fields

    @staticmethod
    async def process_ocr(credential_id: UUID) -> Dict[str, Any]:
        """
        Process OCR for a credential (called after upload).

        Args:
            credential_id: Credential ID to process

        Returns:
            Updated credential with OCR results
        """
        try:
            # Fetch credential record
            credential_response = supabase.table("vault_credentials").select("*").eq("id", str(credential_id)).execute()
            credential = credential_response.data[0] if credential_response.data else None

            if not credential:
                raise ValueError(f"Credential not found: {credential_id}")

            # Download file from storage
            file_path = credential["file_path"]
            file_content = supabase.storage.from_("tenopa-files").download(file_path)

            # Extract text
            extracted_text = await VaultCredentialService.extract_text_from_file(
                credential_id,
                file_content,
                credential["file_format"]
            )

            # Extract structured fields
            extracted_fields = VaultCredentialService._extract_credential_fields(extracted_text)

            # Calculate quality score (basic heuristic)
            quality_score = VaultCredentialService._calculate_quality_score(extracted_text, extracted_fields)

            # Update credential with OCR results
            update_data = {
                "extracted_text": extracted_text,
                "extracted_text_updated_at": datetime.now().isoformat(),
                "ocr_status": "success",
                "credential_issue_date": extracted_fields.get("credential_issue_date"),
                "credential_issuer": extracted_fields.get("credential_issuer"),
                "project_name": extracted_fields.get("project_name"),
                "project_amount": extracted_fields.get("project_amount"),
                "metadata": {
                    **(credential.get("metadata") or {}),
                    "extracted_fields": extracted_fields,
                    "quality_score": quality_score,
                    "manual_review_needed": quality_score < 70
                }
            }

            supabase.table("vault_credentials").update(update_data).eq("id", str(credential_id)).execute()

            logger.info(f"OCR completed for credential {credential_id}: quality_score={quality_score}")

            return {
                "id": str(credential_id),
                "ocr_status": "success",
                "quality_score": quality_score,
                "extracted_fields": extracted_fields
            }

        except Exception as e:
            logger.error(f"OCR processing failed for {credential_id}: {str(e)}")
            # Update credential with error status
            try:
                supabase.table("vault_credentials").update({
                    "ocr_status": "failed",
                    "ocr_error_message": str(e)
                }).eq("id", str(credential_id)).execute()
            except Exception as inner_e:
                logger.error(f"Failed to update OCR error status: {str(inner_e)}")
            raise

    @staticmethod
    def _calculate_quality_score(extracted_text: str, extracted_fields: Dict[str, Any]) -> int:
        """
        Calculate quality score for extracted content (0-100).

        Factors:
        - Text length (should have meaningful content)
        - Number of extracted fields
        - Presence of key credential markers
        """
        score = 0

        # Text length factor (max 40 points)
        text_length = len(extracted_text.strip())
        if text_length > 500:
            score += 40
        elif text_length > 200:
            score += 30
        elif text_length > 100:
            score += 20
        elif text_length > 50:
            score += 10

        # Extracted fields factor (max 40 points)
        num_fields = len(extracted_fields)
        if num_fields >= 5:
            score += 40
        elif num_fields >= 4:
            score += 30
        elif num_fields >= 3:
            score += 20
        elif num_fields >= 2:
            score += 10

        # Presence of key markers (max 20 points)
        key_markers = ["증명", "발급", "기관", "년", "월", "일", "원"]
        marker_count = sum(1 for marker in key_markers if marker in extracted_text)
        score += min(20, marker_count * 3)

        return min(100, score)

    @staticmethod
    async def get_credential(credential_id: UUID) -> Dict[str, Any]:
        """Fetch credential details"""
        response = supabase.table("vault_credentials").select("*").eq("id", str(credential_id)).execute()
        return response.data[0] if response.data else None

    @staticmethod
    async def list_credentials(project_id: UUID, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List credentials for a project"""
        response = supabase.table("vault_credentials")\
            .select("*")\
            .eq("completed_project_id", str(project_id))\
            .is_("deleted_at", "null")\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()

        total_response = supabase.table("vault_credentials")\
            .select("id", count="exact")\
            .eq("completed_project_id", str(project_id))\
            .is_("deleted_at", "null")\
            .execute()

        return {
            "credentials": response.data,
            "total": total_response.count,
            "limit": limit,
            "offset": offset
        }

    @staticmethod
    async def delete_credential(credential_id: UUID) -> Dict[str, Any]:
        """Soft delete a credential"""
        update_data = {"deleted_at": datetime.now().isoformat()}
        response = supabase.table("vault_credentials").update(update_data).eq("id", str(credential_id)).execute()
        return response.data[0] if response.data else None
