"""
Enhanced Document Processor with Smart Chunking
Improvements:
- Token-based chunking (not character-based)
- Section-aware splitting (preserves activities, questions, code blocks)
- Context windows for better retrieval
- Enriched metadata
- Vietnamese text preprocessing
"""

import logging
import re
import argparse
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


class EnhancedDocumentProcessor:
    """Enhanced processor with smart chunking for Vietnamese educational content"""

    def __init__(
        self,
        subject: Optional[str] = None,
        chunk_size: int = 512,  # tokens
        chunk_overlap: int = 50,  # tokens
        encoding_name: str = "cl100k_base",
        smart_chunking: bool = True,
        add_context_windows: bool = True
    ):
        self.subject = subject
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
        self.smart_chunking = smart_chunking
        self.add_context_windows = add_context_windows

        logger.info(f"EnhancedDocumentProcessor initialized:")
        logger.info(f"  - Chunk size: {chunk_size} tokens")
        logger.info(f"  - Overlap: {chunk_overlap} tokens")
        logger.info(f"  - Smart chunking: {smart_chunking}")
        logger.info(f"  - Context windows: {add_context_windows}")

    def process_txt(self, txt_path: str | Path, output_dir: Optional[str | Path] = None) -> List[Dict]:
        """Process TXT file with enhanced chunking"""
        txt_path = Path(txt_path)
        logger.info(f"📄 Processing: {txt_path.name}")

        if not txt_path.exists():
            raise FileNotFoundError(f"File not found: {txt_path}")

        # Load text
        with open(txt_path, "r", encoding="utf-8", errors='replace') as f:
            full_text = f.read().strip()

        if not full_text:
            logger.error("Empty file")
            return []

        # Detect metadata
        subject_info = self._detect_subject(txt_path.name, full_text)
        grade, education_level = self._detect_grade(txt_path.name)

        # Preprocess
        full_text = self._preprocess_text(full_text)

        # Build chapter map
        chapter_map = self._build_chapter_map(full_text)

        # Split into lessons
        lessons = self._split_into_lessons(full_text)
        logger.info(f"📚 Found {len(lessons)} lessons")

        all_chunks = []
        chunk_id = 0

        for lesson_idx, lesson_text in enumerate(lessons):
            # Extract lesson metadata
            metadata = self._extract_lesson_metadata(lesson_text, subject_info, grade, education_level)

            # Map to chapter
            lesson_num = metadata.get('lesson_number')
            if lesson_num and not metadata.get('chapter'):
                chapter_info = chapter_map.get(lesson_num)
                if chapter_info:
                    metadata.update(chapter_info)

            logger.info(f"  Lesson {lesson_num}: {metadata.get('lesson_title', 'N/A')}")

            # Smart chunking
            if self.smart_chunking:
                chunks = self._smart_chunk_by_sections(lesson_text, metadata)
            else:
                chunks = self._basic_chunk(lesson_text, metadata)

            # Add context windows
            if self.add_context_windows:
                chunks = self._add_context_windows(chunks)

            # Enrich metadata
            chunks = [self._enrich_metadata(c) for c in chunks]

            # Assign IDs
            for chunk in chunks:
                chunk['chunk_id'] = f"{txt_path.stem}_{chunk_id:04d}"
                chunk['source_file'] = txt_path.name
                chunk['lesson_index'] = lesson_idx
                chunk_id += 1
                all_chunks.append(chunk)

        logger.info(f"✅ Created {len(all_chunks)} chunks")

        # Save if output directory specified
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{txt_path.stem}_chunks.json"
            self._save_chunks(all_chunks, output_path)
            logger.info(f"💾 Saved to {output_path}")

        return all_chunks

    def _preprocess_text(self, text: str) -> str:
        """Enhanced preprocessing for Vietnamese text"""
        # Remove page markers
        text = re.sub(r'--- PAGE \d+ ---', '', text)

        # Remove repeated headers
        text = re.sub(r'^(TIN HỌC \d+|KẾT NỐI TRI THỨC|NHÀ XUẤT BẢN|BỘ GIÁO DỤC)$',
                      '', text, flags=re.MULTILINE | re.IGNORECASE)

        # Remove TOC entries
        text = re.sub(r'^.+?\s{5,}\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^(?:Bài|Chủ đề)\s+\d+[A-Z]?[\.\s:]+.+?,\s*(?:Trang|trang)\s+\d+\s*$',
                      '', text, flags=re.MULTILINE | re.IGNORECASE)

        # Normalize whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)

        # Remove very short lines (noise)
        lines = text.split('\n')
        cleaned = [line for line in lines if len(line.strip()) > 3 or line.strip() == '']
        text = '\n'.join(cleaned)

        return text.strip()

    def _smart_chunk_by_sections(self, text: str, metadata: Dict) -> List[Dict]:
        """Smart chunking that preserves semantic boundaries"""

        # Define semantic boundary patterns
        section_patterns = [
            (r'HOẠT ĐỘNG\s+\d+', 'activity'),
            (r'Hoạt động\s+\d+', 'activity'),
            (r'Câu hỏi\s+\d+', 'question'),
            (r'Bài tập\s+\d+', 'exercise'),
            (r'VÍ DỤ\s+\d+', 'example'),
            (r'Ví dụ\s+\d+', 'example'),
            (r'```[\s\S]*?```', 'code_block'),  # Code blocks
            (r'^\d+\.\s+[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ]', 'section_heading'),
        ]

        sections = self._split_by_semantic_boundaries(text, section_patterns)

        chunks = []
        for section_text, section_type in sections:
            section_meta = metadata.copy()
            section_meta['section_type'] = section_type

            token_count = self._count_tokens(section_text)

            # Keep small sections intact
            if token_count <= self.chunk_size:
                chunks.append({
                    'content': section_text,
                    'metadata': section_meta,
                    'token_count': token_count,
                    'char_count': len(section_text),
                    'is_complete_section': True
                })
            else:
                # Split large sections with more overlap to preserve context
                sub_chunks = self._split_large_section(section_text, section_meta)
                chunks.extend(sub_chunks)

        return chunks

    def _split_by_semantic_boundaries(self, text: str, patterns: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Split text by semantic patterns"""

        # Find all matches
        matches = []
        for pattern, section_type in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                matches.append((match.start(), match.end(), section_type))

        # Sort by position
        matches.sort(key=lambda x: x[0])

        if not matches:
            return [(text, 'general')]

        sections = []
        prev_end = 0

        for i, (start, end, section_type) in enumerate(matches):
            # Text before this match
            if start > prev_end:
                before_text = text[prev_end:start].strip()
                if before_text and len(before_text) > 10:
                    sections.append((before_text, 'general'))

            # Section content (from match to next match or end)
            next_start = matches[i + 1][0] if i + 1 < len(matches) else len(text)
            section_content = text[start:next_start].strip()
            if section_content:
                sections.append((section_content, section_type))

            prev_end = next_start

        return sections

    def _split_large_section(self, text: str, metadata: Dict) -> List[Dict]:
        """Split large sections while preserving context"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap * 2,  # More overlap for sections
            length_function=self._count_tokens,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )

        sub_texts = splitter.split_text(text)

        chunks = []
        for idx, sub_text in enumerate(sub_texts):
            chunk_meta = metadata.copy()
            chunk_meta['sub_section_index'] = idx
            chunk_meta['total_sub_sections'] = len(sub_texts)

            chunks.append({
                'content': sub_text,
                'metadata': chunk_meta,
                'token_count': self._count_tokens(sub_text),
                'char_count': len(sub_text),
                'is_complete_section': False
            })

        return chunks

    def _basic_chunk(self, text: str, metadata: Dict) -> List[Dict]:
        """Token-based basic chunking"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=self._count_tokens,  # Use token counter
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
        )

        chunks = []
        for chunk_text in splitter.split_text(text):
            chunk = {
                'content': chunk_text,
                'metadata': metadata.copy(),
                'token_count': self._count_tokens(chunk_text),
                'char_count': len(chunk_text)
            }
            chunks.append(chunk)

        return chunks

    def _add_context_windows(self, chunks: List[Dict]) -> List[Dict]:
        """Add context from previous/next chunks"""
        for i, chunk in enumerate(chunks):
            # Previous chunk preview
            if i > 0:
                chunk['metadata']['prev_chunk_preview'] = chunks[i-1]['content'][-100:]

            # Next chunk preview
            if i < len(chunks) - 1:
                chunk['metadata']['next_chunk_preview'] = chunks[i+1]['content'][:100]

            # Position info
            chunk['metadata']['chunk_position'] = {
                'index': i,
                'total': len(chunks),
                'relative_position': round(i / max(len(chunks) - 1, 1), 2)
            }

        return chunks

    def _enrich_metadata(self, chunk: Dict) -> Dict:
        """Enrich metadata with content analysis"""
        content = chunk['content']
        metadata = chunk['metadata']

        # Detect content types
        content_types = []
        if re.search(r'HOẠT ĐỘNG|Hoạt động', content, re.IGNORECASE):
            content_types.append('activity')
        if re.search(r'Câu hỏi|Hỏi', content, re.IGNORECASE):
            content_types.append('question')
        if re.search(r'VÍ DỤ|Ví dụ', content, re.IGNORECASE):
            content_types.append('example')
        if re.search(r'```|def |class |import |print\(', content):
            content_types.append('code')
        if re.search(r'Bài tập|Thực hành|Luyện tập', content, re.IGNORECASE):
            content_types.append('exercise')

        metadata['content_types'] = content_types

        # Extract key terms
        metadata['key_terms'] = self._extract_key_terms(content)

        # Content density metrics
        metadata['content_density'] = {
            'char_per_token': round(chunk['char_count'] / max(chunk['token_count'], 1), 2),
            'has_formulas': bool(re.search(r'[=+\-*/^()]', content)),
            'has_lists': bool(re.search(r'^\s*[-•\d]\s', content, re.MULTILINE)),
            'has_code': 'code' in content_types
        }

        return chunk

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text"""
        terms = set()

        # Technical acronyms
        acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
        terms.update(acronyms)

        # Vietnamese capitalized terms
        viet_terms = re.findall(r'\b[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][a-zàáâãèéêìíòóôõùúýăđĩũơưếềểễệ]+\b', text)
        terms.update(viet_terms)

        return list(terms)[:10]

    # ... (Include other helper methods from original document_processor.py)
    # _build_chapter_map, _split_into_lessons, _extract_lesson_metadata, etc.
    # (These remain the same from the original)

    def _build_chapter_map(self, text: str) -> Dict[int, Dict]:
        """Build lesson -> chapter mapping"""
        # Same as original implementation
        chapter_map = {}
        items = []

        chapter_patterns = [
            r"CHỦ ĐỀ\s+(\d+)[\.\s:：-]+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^\n\r]+)",
            r"Chủ đề\s+(\d+)[\.\s:：-]+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^\n\r]+)",
        ]

        lesson_patterns = [
            r"BÀI\s+(\d+)[A-Z]?[\.\s:：-]",
            r"Bài\s+(\d+)[A-Z]?[\.\s:：-]",
        ]

        # Find chapters
        for pattern in chapter_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                chapter_num = int(match.group(1))
                chapter_title = match.group(2).strip()
                items.append({
                    'type': 'CHAPTER',
                    'position': match.start(),
                    'number': chapter_num,
                    'title': chapter_title,
                    'full': f"Chủ đề {chapter_num}. {chapter_title}"
                })

        # Find lessons
        for pattern in lesson_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                lesson_num = int(match.group(1))
                items.append({
                    'type': 'LESSON',
                    'position': match.start(),
                    'number': lesson_num
                })

        items.sort(key=lambda x: x['position'])

        # Map lessons to chapters
        for i, item in enumerate(items):
            if item['type'] == 'LESSON':
                lesson_num = item['number']

                # Find nearest chapter before
                nearest_chapter = None
                for j in range(i - 1, -1, -1):
                    if items[j]['type'] == 'CHAPTER':
                        nearest_chapter = items[j]
                        break

                if nearest_chapter:
                    chapter_map[lesson_num] = {
                        'chapter': nearest_chapter['full'],
                        'chapter_number': nearest_chapter['number'],
                        'chapter_title': nearest_chapter['title']
                    }

        return chapter_map

    def _split_into_lessons(self, text: str) -> List[str]:
        """Split text into lessons"""
        # Simplified version - use patterns from original
        lesson_patterns = [
            r"BÀI\s+(\d+)[A-Z]?[\.\s:：-]+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^\n\r]+)",
            r"Bài\s+(\d+)[A-Z]?[\.\s:：-]+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^\n\r]+)",
        ]

        markers = []
        for pattern in lesson_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                markers.append((match.start(), match.group(0)))

        markers.sort(key=lambda x: x[0])

        if not markers:
            return [text]

        lessons = []
        for i, (start, _) in enumerate(markers):
            end = markers[i + 1][0] if i + 1 < len(markers) else len(text)
            lesson_text = text[start:end].strip()
            if len(lesson_text) > 100:  # Filter too short
                lessons.append(lesson_text)

        return lessons

    def _extract_lesson_metadata(self, lesson_text: str, subject_info: Dict, grade: int, education_level: str) -> Dict:
        """Extract metadata from lesson"""
        metadata = {
            **subject_info,
            "grade": grade,
            "education_level": education_level,
        }

        # Extract lesson info
        lesson_pattern = r"(?:BÀI|Bài)\s+(\d+)[A-Z]?[\.\s:：-]+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^\n\r]+)"
        match = re.search(lesson_pattern, lesson_text, re.IGNORECASE)

        if match:
            metadata["lesson_number"] = int(match.group(1))
            metadata["lesson_title"] = match.group(2).strip()

        # Content flags
        metadata["has_questions"] = bool(re.search(r"Câu hỏi", lesson_text, re.IGNORECASE))
        metadata["has_activities"] = bool(re.search(r"HOẠT ĐỘNG|Hoạt động", lesson_text, re.IGNORECASE))
        metadata["has_exercises"] = bool(re.search(r"Bài tập|Thực hành", lesson_text, re.IGNORECASE))
        metadata["has_code"] = bool(re.search(r"```|def |class |import ", lesson_text))

        return metadata

    def _detect_subject(self, filename: str, text: str = "") -> Dict:
        """Detect subject from filename"""
        name = filename.lower()
        if "tin" in name or "tin học" in text.lower():
            return {"subject": "Tin học", "subject_key": "tin_hoc"}
        return {"subject": "Unknown", "subject_key": "unknown"}

    def _detect_grade(self, filename: str) -> Tuple[Optional[int], Optional[str]]:
        """Detect grade from filename"""
        match = re.search(r"(\d+)", filename)
        grade = int(match.group(1)) if match else None

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

    def _count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken"""
        return len(self.encoding.encode(text))

    def _save_chunks(self, chunks: List[Dict], output_file: Path):
        """Save chunks to JSON"""
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Enhanced Document Processor")
    parser.add_argument("--input", required=True, help="Input TXT file or directory")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--chunk-size", type=int, default=512, help="Chunk size in tokens")
    parser.add_argument("--chunk-overlap", type=int, default=50, help="Chunk overlap in tokens")
    parser.add_argument("--no-smart-chunking", action="store_true", help="Disable smart chunking")
    parser.add_argument("--no-context-windows", action="store_true", help="Disable context windows")

    args = parser.parse_args()

    processor = EnhancedDocumentProcessor(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        smart_chunking=not args.no_smart_chunking,
        add_context_windows=not args.no_context_windows
    )

    input_path = Path(args.input)

    if input_path.is_dir():
        for txt_file in input_path.glob("*.txt"):
            processor.process_txt(txt_file, args.output)
    else:
        processor.process_txt(input_path, args.output)

    print("\n✅ Processing complete!")


if __name__ == "__main__":
    main()
