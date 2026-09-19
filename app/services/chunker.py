from typing import List, Dict, Any, Optional
import io
from pypdf import PdfReader


class TextChunker:
    def __init__(self, chunk_size: int = 600, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_plain_text(self, text: str) -> List[Dict[str, Any]]:
        """Splits arbitrary text into overlapping chunks."""
        chunks = []
        start = 0
        text_len = len(text)
        index = 0

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk_content = text[start:end].strip()
            
            if chunk_content:
                chunks.append({
                    "chunk_index": index,
                    "content": chunk_content,
                    "page_number": None
                })
                index += 1

            if end == text_len:
                break
            start += (self.chunk_size - self.overlap)

        return chunks

    def chunk_pdf(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """Extracts and chunks page-by-page to retain accurate citation references."""
        reader = PdfReader(io.BytesIO(file_bytes))
        chunks = []
        global_index = 0

        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            start = 0
            text_len = len(page_text)

            while start < text_len:
                end = min(start + self.chunk_size, text_len)
                chunk_content = page_text[start:end].strip()

                if chunk_content:
                    chunks.append({
                        "chunk_index": global_index,
                        "content": chunk_content,
                        "page_number": page_num
                    })
                    global_index += 1

                if end == text_len:
                    break
                start += (self.chunk_size - self.overlap)

        return chunks


chunker_service = TextChunker()
