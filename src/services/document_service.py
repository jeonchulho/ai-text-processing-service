"""
Document service for parsing various document formats.

This service handles document parsing for PDF, DOCX, and TXT files.
"""

from typing import Optional
import io
import structlog
from PyPDF2 import PdfReader
from docx import Document

from src.core.exceptions import ValidationError

logger = structlog.get_logger(__name__)


class DocumentService:
    """Service for document parsing operations."""

    def parse_pdf(self, file_content: bytes) -> str:
        """
        Parse PDF file and extract text.

        Args:
            file_content: PDF file content as bytes

        Returns:
            Extracted text
        """
        try:
            pdf_file = io.BytesIO(file_content)
            reader = PdfReader(pdf_file)

            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())

            text = "\n\n".join(text_parts)
            logger.info(f"Parsed PDF: {len(text)} characters extracted")

            return text

        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            raise ValidationError(f"Failed to parse PDF: {e}")

    def parse_docx(self, file_content: bytes) -> str:
        """
        Parse DOCX file and extract text.

        Args:
            file_content: DOCX file content as bytes

        Returns:
            Extracted text
        """
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)

            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)

            text = "\n\n".join(text_parts)
            logger.info(f"Parsed DOCX: {len(text)} characters extracted")

            return text

        except Exception as e:
            logger.error(f"DOCX parsing error: {e}")
            raise ValidationError(f"Failed to parse DOCX: {e}")

    def parse_text(self, file_content: bytes) -> str:
        """
        Parse plain text file.

        Args:
            file_content: Text file content as bytes

        Returns:
            Extracted text
        """
        try:
            text = file_content.decode('utf-8')
            logger.info(f"Parsed text file: {len(text)} characters")

            return text

        except UnicodeDecodeError:
            # Try other encodings
            try:
                text = file_content.decode('latin-1')
                logger.info(f"Parsed text file (latin-1): {len(text)} characters")
                return text
            except Exception as e:
                logger.error(f"Text decoding error: {e}")
                raise ValidationError(f"Failed to decode text file: {e}")

        except Exception as e:
            logger.error(f"Text parsing error: {e}")
            raise ValidationError(f"Failed to parse text file: {e}")

    def parse_document(
        self,
        file_content: bytes,
        file_type: str
    ) -> str:
        """
        Parse document based on file type.

        Args:
            file_content: File content as bytes
            file_type: File type (pdf, docx, txt)

        Returns:
            Extracted text
        """
        file_type = file_type.lower()

        if file_type == "pdf":
            return self.parse_pdf(file_content)
        elif file_type == "docx":
            return self.parse_docx(file_content)
        elif file_type in ["txt", "text"]:
            return self.parse_text(file_content)
        else:
            raise ValidationError(f"Unsupported file type: {file_type}")


# Global document service instance
document_service = DocumentService()
