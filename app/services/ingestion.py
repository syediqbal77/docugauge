import hashlib
import io
from typing import Tuple, List, Optional
from pypdf import PdfReader
import docx


class IngestionService:
    @staticmethod
    def calculate_sha256(file_bytes: bytes) -> str:
        """Generate a SHA-256 hash from raw file bytes."""
        hasher = hashlib.sha256()
        hasher.update(file_bytes)
        return hasher.hexdigest()

    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> Tuple[str, Optional[int]]:
        """
        Extract text and optional total page count based on file extension.
        Returns: (extracted_text, total_pages)
        """
        ext = filename.lower().split('.')[-1]
        
        if ext == "pdf":
            reader = PdfReader(io.BytesIO(file_bytes))
            total_pages = len(reader.pages)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n\n".join(text_parts), total_pages

        elif ext in ["docx", "doc"]:
            doc = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text])
            return text, None

        elif ext in ["txt", "md"]:
            return file_bytes.decode("utf-8", errors="ignore"), None

        else:
            raise ValueError(f"Unsupported file format: .{ext}")


ingestion_service = IngestionService()
