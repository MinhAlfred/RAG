"""Document Processor - Phase 1 Logic"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple
import re

from pdf2image import convert_from_path
import cv2
import numpy as np
import pytesseract

from ..models.document import DocumentMetadata, Chunk
from ..utils.file_utils import save_json
from config.settings import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Xử lý PDF thành chunks"""

    def __init__(
            self,
            use_ocr: bool = True,
            dpi: int = None,
            chunk_size: int = None,
            chunk_overlap: int = None
    ):
        self.use_ocr = use_ocr
        self.dpi = dpi or settings.OCR_DPI
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        logger.info(f"DocumentProcessor initialized (OCR={use_ocr}, DPI={self.dpi})")

    def process_pdf(
            self,
            pdf_path: str | Path,
            output_dir: Optional[str | Path] = None
    ) -> List[Chunk]:
        """
        Process PDF file thành chunks

        Args:
            pdf_path: Path to PDF
            output_dir: Directory to save processed chunks

        Returns:
            List of Chunk objects
        """
        pdf_path = Path(pdf_path)
        logger.info(f"Processing PDF: {pdf_path.name}")

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Extract grade from filename
        grade, education_level = self._detect_grade(pdf_path.name)

        # Convert PDF to images
        images = convert_from_path(str(pdf_path), dpi=self.dpi)
        logger.info(f"Converted {len(images)} pages to images")

        # Process each page
        pages_data = []
        for page_num, image in enumerate(images, 1):
            logger.debug(f"Processing page {page_num}/{len(images)}")

            # Convert PIL to OpenCV
            opencv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Extract text
            text = self._extract_text_opencv(opencv_img, page_num)

            pages_data.append({
                'page_number': page_num,
                'text': text,
                'grade': grade,
                'education_level': education_level
            })

        # Identify structure
        pages_data = self._identify_structure(pages_data)

        # Create chunks
        chunks = self._create_chunks(pages_data, pdf_path.name)

        logger.info(f"Created {len(chunks)} chunks from {pdf_path.name}")

        # Save if output_dir provided
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            output_file = output_dir / f"{pdf_path.stem}_processed.json"
            chunk_dicts = [chunk.to_dict() for chunk in chunks]
            save_json(chunk_dicts, output_file)
            logger.info(f"Saved to {output_file}")

        return chunks

    def _detect_grade(self, filename: str) -> Tuple[Optional[int], Optional[str]]:
        """Detect grade from filename"""
        grade_match = re.search(r'(?:lop|lớp|grade)[\s_-]*(\d+)', filename.lower())

        if grade_match:
            grade = int(grade_match.group(1))
            if grade <= 5:
                level = "Tiểu học"
            elif grade <= 9:
                level = "THCS"
            else:
                level = "THPT"
            return grade, level

        return None, None

    def _extract_text_opencv(self, image: np.ndarray, page_num: int) -> str:
        """Extract text using OpenCV + OCR"""
        if not self.use_ocr:
            return ""

        # Preprocess
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Detect text regions
        bboxes = self._detect_text_regions(binary)

        # OCR each region
        texts = []
        for bbox in bboxes:
            x, y, w, h = bbox
            roi = image[y:y + h, x:x + w]

            try:
                text = pytesseract.image_to_string(
                    roi,
                    lang=settings.OCR_LANGUAGE,
                    config='--psm 6'
                )
                if text.strip():
                    texts.append(text.strip())
            except Exception as e:
                logger.warning(f"OCR error on page {page_num}: {e}")

        return "\n\n".join(texts)

    def _detect_text_regions(self, binary: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect text regions using contours"""
        # Dilate to merge characters
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 5))
        dilated = cv2.dilate(binary, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Extract bounding boxes
        bboxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w * h > 500 and h > 10:  # Filter small boxes
                bboxes.append((x, y, w, h))

        # Sort top to bottom
        bboxes = sorted(bboxes, key=lambda b: (b[1], b[0]))

        return bboxes

    def _identify_structure(self, pages_data: List[dict]) -> List[dict]:
        """Identify chapters and sections"""
        chapter_pattern = re.compile(r'Chương\s+(\d+)[:\s.]*(.+)', re.IGNORECASE)
        section_pattern = re.compile(r'Bài\s+(\d+)[:\s.]*(.+)', re.IGNORECASE)

        current_chapter = None
        current_chapter_title = None
        current_section = None

        for page in pages_data:
            text = page['text']

            # Find chapter
            chapter_match = chapter_pattern.search(text)
            if chapter_match:
                current_chapter = int(chapter_match.group(1))
                current_chapter_title = chapter_match.group(2).strip()

            # Find section
            section_match = section_pattern.search(text)
            if section_match:
                current_section = f"Bài {section_match.group(1)}: {section_match.group(2).strip()}"

            page['chapter'] = current_chapter
            page['chapter_title'] = current_chapter_title
            page['section'] = current_section

        return pages_data

    def _create_chunks(self, pages_data: List[dict], source_file: str) -> List[Chunk]:
        """Create chunks from pages"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        chunks = []
        chunk_id = 0

        for page in pages_data:
            if not page['text'].strip():
                continue

            # Split text
            text_chunks = splitter.split_text(page['text'])

            for chunk_text in text_chunks:
                metadata = DocumentMetadata(
                    source_file=source_file,
                    page_number=page['page_number'],
                    grade=page.get('grade'),
                    education_level=page.get('education_level'),
                    chapter=page.get('chapter'),
                    chapter_title=page.get('chapter_title'),
                    section=page.get('section'),
                    extraction_method="opencv_ocr" if self.use_ocr else "text"
                )

                chunk = Chunk(
                    chunk_id=f"{source_file}_{chunk_id}",
                    content=chunk_text,
                    metadata=metadata
                )

                chunks.append(chunk)
                chunk_id += 1

        return chunks
