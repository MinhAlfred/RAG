"""Document Processor - Generic for all subjects"""

import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import pdfplumber
import tiktoken

from ..models.document import DocumentMetadata, Chunk
from ..utils.file_utils import save_json
from config.settings import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Generic Document Processor for all subjects"""

    def __init__(
            self,
            subject: Optional[str] = None,  # Auto-detect if None
            chunk_size: int = None,
            chunk_overlap: int = None,
            encoding_name: str = "cl100k_base"
    ):
        self.subject_key = subject
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.encoding = tiktoken.get_encoding(encoding_name)

        logger.info(f"DocumentProcessor initialized (subject={subject or 'auto'})")

    def process_pdf(
            self,
            pdf_path: str | Path,
            output_dir: Optional[str | Path] = None,
            subject: Optional[str] = None  # Override auto-detection
    ) -> List[Chunk]:
        """
        Process PDF file - Generic for all subjects

        Args:
            pdf_path: Path to PDF
            output_dir: Directory to save processed chunks
            subject: Override subject detection

        Returns:
            List of Chunk objects
        """
        pdf_path = Path(pdf_path)
        logger.info(f"📖 Processing PDF: {pdf_path.name}")

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Detect subject
        detected_subject = subject or self.subject_key or settings.detect_subject_from_filename(pdf_path.name)

        if detected_subject:
            subject_config = settings.get_subject_config(detected_subject)
            subject_name = subject_config['name'] if subject_config else detected_subject
            logger.info(f"   📚 Subject: {subject_name}")
        else:
            logger.warning(f"   ⚠️  Subject not detected, using generic patterns")
            subject_config = None
            subject_name = "Unknown"

        # Detect grade
        grade, education_level = self._detect_grade(pdf_path.name)
        logger.info(f"   🎓 Grade: {grade} ({education_level})")

        # Extract text from PDF
        pages_data = self._extract_text_from_pdf(
            pdf_path,
            grade,
            education_level,
            detected_subject,
            subject_name
        )
        logger.info(f"   ✓ Extracted {len(pages_data)} pages")

        # Identify structure using subject-specific patterns
        pages_data = self._identify_structure(pages_data, subject_config)

        # Create chunks
        chunks = self._create_chunks(pages_data, pdf_path.name)
        logger.info(f"✅ Created {len(chunks)} chunks from {pdf_path.name}")

        # Save if output_dir provided
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Organize by subject and grade
            if detected_subject and grade:
                output_file = output_dir / f"{detected_subject}_lop_{grade}_chunks.json"
            else:
                output_file = output_dir / f"{pdf_path.stem}_chunks.json"

            self._save_chunks(chunks, output_file)
            logger.info(f"💾 Saved to {output_file}")

        return chunks

    def _extract_text_from_pdf(
            self,
            pdf_path: Path,
            grade: Optional[int],
            education_level: Optional[str],
            subject_key: Optional[str],
            subject_name: str
    ) -> List[dict]:
        """Extract text from PDF using pdfplumber"""
        pages_data = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text
                text = page.extract_text() or ""

                # Extract tables
                tables = page.extract_tables()
                if tables:
                    table_text = self._format_tables(tables)
                    text += "\n\n" + table_text

                # Check text validity
                if self._is_text_valid(text):
                    extraction_method = "text"
                else:
                    logger.warning(f"   ⚠️  Page {page_num}: Poor text extraction")
                    extraction_method = "text_poor"

                pages_data.append({
                    'page_number': page_num,
                    'text': text.strip(),
                    'grade': grade,
                    'education_level': education_level,
                    'subject': subject_name,
                    'subject_key': subject_key,
                    'has_tables': len(tables) > 0,
                    'extraction_method': extraction_method
                })

        return pages_data

    def _format_tables(self, tables: List) -> str:
        """Format tables as text"""
        formatted = []
        for table in tables:
            rows = []
            for row in table:
                row_text = " | ".join([str(cell) if cell else "" for cell in row])
                rows.append(row_text)

            table_text = "\n".join(rows)
            formatted.append(f"[BẢNG]\n{table_text}\n[/BẢNG]")

        return "\n\n".join(formatted)

    def _is_text_valid(self, text: str) -> bool:
        """Check if extracted text is valid"""
        if not text or len(text.strip()) < 50:
            return False

        # Check for weird characters
        weird_chars = sum(1 for c in text if ord(c) > 127 and c not in
                          'àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđĐ')

        if len(text) > 0 and weird_chars / len(text) > 0.3:
            return False

        return True

    def _detect_grade(self, filename: str) -> Tuple[Optional[int], Optional[str]]:
        """Detect grade from filename"""
        filename_lower = filename.lower()

        grade_match = re.search(r'(?:lop|lớp|grade)[\s_-]*(\d+)', filename_lower)

        if grade_match:
            grade = int(grade_match.group(1))
        else:
            number_match = re.search(r'(\d+)', filename_lower)
            grade = int(number_match.group(1)) if number_match else None

        if grade:
            if grade <= 5:
                level = "Tiểu học"
            elif grade <= 9:
                level = "THCS"
            else:
                level = "THPT"
        else:
            level = None

        return grade, level

    def _identify_structure(
            self,
            pages_data: List[dict],
            subject_config: Optional[Dict]
    ) -> List[dict]:
        """Identify structure using subject-specific patterns"""

        # Use subject-specific patterns if available
        if subject_config:
            chapter_patterns = [re.compile(p, re.IGNORECASE)
                                for p in subject_config.get('chapter_patterns', [])]
            section_patterns = [re.compile(p, re.IGNORECASE)
                                for p in subject_config.get('section_patterns', [])]
        else:
            # Generic patterns
            chapter_patterns = [
                re.compile(r'Chương\s+(\d+)[:\s.]*(.+)', re.IGNORECASE),
                re.compile(r'Phần\s+(\d+)[:\s.]*(.+)', re.IGNORECASE),
            ]
            section_patterns = [
                re.compile(r'Bài\s+(\d+)[:\s.]*(.+)', re.IGNORECASE),
            ]

        current_chapter = None
        current_chapter_title = None
        current_section = None

        for page in pages_data:
            text = page['text']

            # Find chapter
            for pattern in chapter_patterns:
                match = pattern.search(text)
                if match:
                    chapter_num = match.group(1)
                    if chapter_num.isdigit():
                        current_chapter = int(chapter_num)
                    else:
                        current_chapter = self._roman_to_int(chapter_num)
                    current_chapter_title = match.group(2).strip()
                    break

            # Find section
            for pattern in section_patterns:
                match = pattern.search(text)
                if match:
                    section_num = match.group(1)
                    section_title = match.group(2).strip()
                    current_section = f"Bài {section_num}: {section_title}"
                    break

            # Add structure info
            page['chapter'] = current_chapter
            page['chapter_title'] = current_chapter_title
            page['section'] = current_section

            # Extract topics using subject-specific keywords
            page['topics'] = self._extract_topics(text, page.get('subject_key'), page.get('education_level'))

            # Detect content types
            page['has_code'] = self._detect_code(text)
            page['has_formula'] = self._detect_formula(text)
            page['has_diagram'] = self._detect_diagram(text)

        return pages_data

    def _roman_to_int(self, s: str) -> int:
        """Convert Roman numerals"""
        roman = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
        total = 0
        prev = 0

        for char in reversed(s.upper()):
            val = roman.get(char, 0)
            if val < prev:
                total -= val
            else:
                total += val
            prev = val

        return total or 1

    def _extract_topics(
            self,
            text: str,
            subject_key: Optional[str],
            education_level: Optional[str]
    ) -> List[str]:
        """Extract topics using subject-specific keywords"""

        # Get subject-specific keywords
        if subject_key:
            subject_config = settings.get_subject_config(subject_key)
            keywords = subject_config.get('keywords', []) if subject_config else []
        else:
            keywords = []

        # Find keywords in text
        text_lower = text.lower()
        found_topics = [kw for kw in keywords if kw in text_lower]

        return list(set(found_topics))[:10]  # Max 10 topics

    def _detect_code(self, text: str) -> bool:
        """Detect if text contains code (for CS subject)"""
        code_indicators = [
            'def ', 'class ', 'import ', 'for ', 'while ', 'if ',
            'print(', 'input(', 'return ', '```', 'function'
        ]
        return any(indicator in text for indicator in code_indicators)

    def _detect_formula(self, text: str) -> bool:
        """Detect mathematical formulas"""
        formula_indicators = [
            '=', '+', '-', '×', '÷', '²', '³', '√',
            'sin', 'cos', 'tan', 'log', 'lim',
            '∫', '∑', 'π', '≠', '≤', '≥'
        ]
        return any(indicator in text for indicator in formula_indicators)

    def _detect_diagram(self, text: str) -> bool:
        """Detect diagrams/figures"""
        diagram_keywords = [
            'hình', 'sơ đồ', 'biểu đồ', 'đồ thị',
            'figure', 'diagram', 'chart'
        ]
        return any(keyword in text.lower() for keyword in diagram_keywords)

    def _create_chunks(self, pages_data: List[dict], source_file: str) -> List[Chunk]:
        """Create chunks from pages"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        chunk_size = self.chunk_size
        if pages_data and pages_data[0].get('grade'):
            grade = pages_data[0]['grade']
            if grade <= 5:
                chunk_size = min(chunk_size, 600)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )

        chunks = []
        chunk_id = 0

        for page in pages_data:
            if not page['text'].strip():
                continue

            text_chunks = splitter.split_text(page['text'])

            for chunk_text in text_chunks:
                metadata = DocumentMetadata(
                    source_file=source_file,
                    subject=page.get('subject'),
                    subject_key=page.get('subject_key'),
                    page_number=page['page_number'],
                    grade=page.get('grade'),
                    education_level=page.get('education_level'),
                    chapter=page.get('chapter'),
                    chapter_title=page.get('chapter_title'),
                    section=page.get('section'),
                    topics=page.get('topics', []),
                    has_code=page.get('has_code', False),
                    has_table=page.get('has_tables', False),
                    has_formula=page.get('has_formula', False),
                    has_diagram=page.get('has_diagram', False),
                    extraction_method=page.get('extraction_method', 'text')
                )

                chunk = Chunk(
                    chunk_id=f"{source_file}_{chunk_id:04d}",
                    content=chunk_text,
                    metadata=metadata,
                    token_count=self._count_tokens(chunk_text)
                )

                chunks.append(chunk)
                chunk_id += 1

        return chunks

    def _count_tokens(self, text: str) -> int:
        """Count tokens"""
        return len(self.encoding.encode(text))

    def _save_chunks(self, chunks: List[Chunk], output_file: Path):
        """Save chunks to JSON"""
        chunk_dicts = [chunk.to_dict() for chunk in chunks]
        save_json(chunk_dicts, output_file)

    def get_statistics(self, chunks: List[Chunk]) -> dict:
        """Get statistics"""
        if not chunks:
            return {}

        stats = {
            'total_chunks': len(chunks),
            'total_tokens': sum(c.token_count or 0 for c in chunks),
            'avg_tokens_per_chunk': 0,
            'subject': chunks[0].metadata.subject if chunks else None,
            'pages': set(),
            'chapters': set(),
            'grades': set(),
            'has_code': 0,
            'has_formula': 0,
            'has_tables': 0
        }

        for chunk in chunks:
            stats['pages'].add(chunk.metadata.page_number)
            if chunk.metadata.chapter:
                stats['chapters'].add(chunk.metadata.chapter)
            if chunk.metadata.grade:
                stats['grades'].add(chunk.metadata.grade)
            if chunk.metadata.has_code:
                stats['has_code'] += 1
            if chunk.metadata.has_formula:
                stats['has_formula'] += 1
            if chunk.metadata.has_table:
                stats['has_tables'] += 1

        if stats['total_chunks'] > 0:
            stats['avg_tokens_per_chunk'] = stats['total_tokens'] // stats['total_chunks']

        stats['pages'] = len(stats['pages'])
        stats['chapters'] = len(stats['chapters'])
        stats['grades'] = list(stats['grades'])

        return stats