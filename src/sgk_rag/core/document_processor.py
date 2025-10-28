"""
Enhanced Document Processor with Better Metadata Extraction
Optimized for Vietnamese textbooks (especially Tin học)
FIXED: Correctly handles encoding issues and better lesson detection
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


class DocumentProcessor:
    """Enhanced Document Processor for Vietnamese educational content"""

    def __init__(
        self,
        subject: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        encoding_name: str = "cl100k_base",
        smart_chunking: bool = True
    ):
        self.subject = subject
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
        self.smart_chunking = smart_chunking
        
        # Set logging level to DEBUG to see detailed mapping
        logger.setLevel(logging.DEBUG)
        logger.info(f"DocumentProcessor initialized (subject={subject or 'auto'}, smart_chunking={smart_chunking})")

    def process_txt(self, txt_path: str | Path, output_dir: Optional[str | Path] = None) -> List[Dict]:
        """Process a single TXT file with enhanced metadata extraction"""
        txt_path = Path(txt_path)
        logger.info(f"📄 Processing TXT: {txt_path.name}")

        if not txt_path.exists():
            raise FileNotFoundError(f"TXT not found: {txt_path}")

        # 🔥 CRITICAL: Read with UTF-8 with replacement for corrupted chars
        full_text = None

        # Try UTF-8 first with error handling
        try:
            with open(txt_path, "r", encoding="utf-8", errors='replace') as f:
                full_text = f.read().strip()
            logger.info(f"✅ Successfully read file with UTF-8 (with replacement)")
        except Exception as e:
            logger.error(f"❌ Could not read file: {e}")
            return []

        if not full_text:
            logger.error("❌ Empty file content")
            return []

        # Detect subject & grade
        subject_info = self._detect_subject(txt_path.name, full_text)
        grade, education_level = self._detect_grade(txt_path.name)

        # Clean up text
        full_text = self._remove_intro_sections(full_text)
        full_text = self._remove_table_of_contents(full_text)
        full_text = self._preprocess_text(full_text)

        # 🔥 NEW: Build chapter map FIRST
        chapter_map = self._build_chapter_map(full_text)
        logger.info(f"🗺️  Built chapter map: {len(chapter_map)} lessons mapped")

        # 🔥 FIXED: Better lesson splitting
        lessons = self._split_into_lessons(full_text)
        logger.info(f"🧩 Detected {len(lessons)} lessons")

        # Fallback: if no lessons extracted, retry with lenient splitting
        if not lessons:
            logger.warning("⚠️ No lessons extracted; applying fallback splitting without TOC/short-content filters")
            lessons = self._split_into_lessons_fallback(full_text)
            logger.info(f"🧩 Fallback extracted {len(lessons)} lessons")
            if not lessons:
                logger.warning("⚠️ Fallback also found no lessons; using full document as single lesson")
                lessons = [full_text]

        all_chunks = []
        chunk_id = 0

        for lesson_text in lessons:
            # Extract metadata
            metadata = self._extract_lesson_metadata(lesson_text, subject_info, grade, education_level)

            # 🔥 Use chapter_map if no chapter found
            lesson_num = metadata.get('lesson_number')
            if lesson_num and not metadata.get('chapter'):
                chapter_info = chapter_map.get(lesson_num)
                if chapter_info:
                    metadata['chapter'] = chapter_info['chapter']
                    metadata['chapter_number'] = chapter_info['chapter_number']
                    metadata['chapter_title'] = chapter_info['chapter_title']

            logger.info(f"  📚 {metadata.get('chapter') or 'N/A'} | "
                       f"Bài {metadata.get('lesson_number')}: {metadata.get('lesson_title') or 'N/A'}")

            # Chunk lesson
            if self.smart_chunking and metadata.get('sections'):
                chunks = self._smart_chunk_by_sections(lesson_text, metadata)
            else:
                chunks = self._basic_chunk(lesson_text, metadata)

            # Assign chunk_id
            for chunk in chunks:
                chunk['chunk_id'] = f"{txt_path.stem}_{chunk_id:04d}"
                chunk['source_file'] = txt_path.name
                chunk_id += 1
                all_chunks.append(chunk)

        avg_tokens = sum(c['token_count'] for c in all_chunks) // len(all_chunks) if all_chunks else 0
        logger.info(f"✅ Created {len(all_chunks)} chunks (avg {avg_tokens} tokens/chunk)")

        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{txt_path.stem}_chunks.json"
            self._save_chunks(all_chunks, output_path)
            logger.info(f"💾 Saved chunks to {output_path}")

        return all_chunks

    def _remove_intro_sections(self, text: str) -> str:
        """Remove intro sections"""
        patterns = [
            r"HƯỚNG DẪN SỬ DỤNG SÁCH[\s\S]*?(?=CHỦ ĐỀ|MỤC LỤC)",
            r"LỜI NÓI ĐẦU[\s\S]*?(?=CHỦ ĐỀ|MỤC LỤC)",
            # Also handle corrupted encoding
            r"HÆ¯á»›NG DáºªN[\s\S]*?(?=CHá»¦ Äá»€|Má»¤C Lá»¤C)",
        ]
        for pattern in patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        return text

    def _remove_table_of_contents(self, text: str) -> str:
        """Remove table of contents but preserve actual lesson content"""
        # Handle both correct and corrupted encoding
        toc_patterns = [
            r"={50,}\s*MỤC LỤC\s*={50,}[\s\S]*?(?=CHỦ ĐỀ\s+\d+)",
            r"={50,}\s*Má»¤C Lá»¤C\s*={50,}[\s\S]*?(?=CHá»¦ Äá»€\s+\d+)",
            r"MỤC LỤC\s*\n[\s\S]*?(?=CHỦ ĐỀ\s+\d+)",
        ]

        for pattern in toc_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # More precise TOC removal - only remove lines with page numbers at the end
        # This preserves actual lesson content while removing TOC entries
        text = re.sub(r"^(?:Chủ đề|Bài)\s+\d+[A-Z]?\.\s+.+?,\s*Trang\s+\d+\s*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r"^(?:Chủ đề|Bài)\s+\d+[A-Z]?\.\s+.+?\s{5,}\d+\s*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r"^\s*Trang\s*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r"^={50,}\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text

    def _preprocess_text(self, text: str) -> str:
        """Clean up text"""
        # Remove page numbers
        text = re.sub(r"(?:TRANG|Trang|Page)\s+\d+", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^[-=_]{3,}$", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()

    def _build_chapter_map(self, text: str) -> Dict[int, Dict]:
        """
        🔥 ENHANCED: Build lesson -> chapter mapping with improved detection
        Handles both UTF-8 and corrupted encoding, finds ALL chapters
        """
        chapter_map = {}
        items = []

        # Multiple patterns to handle encoding issues and Vietnamese characters
        chapter_patterns = [
            r"CHỦ ĐỀ\s+(\d+)[\.\s:：-]+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^\n\r]+)",
            r"CHá»¦ Äá»€\s+(\d+)[\.\s:：-]+([A-ZÀ-ÝĐỨ][^\n\r]+)",
            r"Chủ đề\s+(\d+)[\.\s:：-]+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^\n\r]+)",
        ]

        lesson_patterns = [
            r"BÀI\s+(\d+)[A-Z]?[\.\s:：-]",
            r"BÃ€I\s+(\d+)[A-Z]?[\.\s:：-]",
            r"Bài\s+(\d+)[A-Z]?[\.\s:：-]",
        ]

        # Find all chapters with detailed logging
        logger.info("🔍 Searching for chapters...")
        for pattern in chapter_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                chapter_num = int(match.group(1))
                chapter_title = re.sub(r'\s+\d+\s*$', '', match.group(2).strip())
                chapter_title = re.sub(r'\s+', ' ', chapter_title).strip()

                items.append({
                    'type': 'CHAPTER',
                    'position': match.start(),
                    'number': chapter_num,
                    'title': chapter_title,
                    'full': f"Chủ đề {chapter_num}. {chapter_title}"
                })
                logger.info(f"  📚 Found: Chủ đề {chapter_num}. {chapter_title} (pos: {match.start()})")

        # Find all lessons
        logger.info("🔍 Searching for lessons...")
        for pattern in lesson_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                lesson_num = int(match.group(1))
                items.append({
                    'type': 'LESSON',
                    'position': match.start(),
                    'number': lesson_num
                })

        # Sort by position
        items.sort(key=lambda x: x['position'])
        logger.info(f"📊 Total items found: {len([x for x in items if x['type'] == 'CHAPTER'])} chapters, {len([x for x in items if x['type'] == 'LESSON'])} lessons")

        # Map lessons to nearest chapter (prefer chapter BEFORE lesson)
        for i, item in enumerate(items):
            if item['type'] == 'LESSON':
                lesson_num = item['number']
                lesson_pos = item['position']

                # Find nearest chapter BEFORE this lesson
                nearest_chapter = None
                min_distance = float('inf')
                
                for j in range(i - 1, -1, -1):
                    if items[j]['type'] == 'CHAPTER':
                        distance = lesson_pos - items[j]['position']
                        if distance >= 0 and distance < min_distance:
                            nearest_chapter = items[j]
                            min_distance = distance
                        break  # Take the first (nearest) chapter before

                # If no chapter before, look ahead (fallback)
                if not nearest_chapter:
                    for j in range(i + 1, len(items)):
                        if items[j]['type'] == 'CHAPTER':
                            nearest_chapter = items[j]
                            break

                if nearest_chapter:
                    chapter_map[lesson_num] = {
                        'chapter': nearest_chapter['full'],
                        'chapter_number': nearest_chapter['number'],
                        'chapter_title': nearest_chapter['title']
                    }
                    logger.debug(f"  📖 Bài {lesson_num} (pos: {lesson_pos}) → {nearest_chapter['full']} (pos: {nearest_chapter.get('position', 'unknown')})")
                else:
                    logger.warning(f"  ⚠️ Bài {lesson_num}: No chapter found!")

        logger.info(f"✅ Chapter mapping completed: {len(chapter_map)} lessons mapped")
        return chapter_map

    def _find_lesson_markers(self, text: str) -> List[Dict]:
        """
        🔥 COMPREHENSIVE: Find all lesson markers with multiple patterns
        Handles all Vietnamese textbook formats found in analysis
        """
        markers = []
        
        # Pattern 1: "BÀI X. TITLE" (uppercase, with dot) - sgk_tin_hoc_7, 8
        pattern1 = r"(?P<full>(?:BÀI|BÃ€I)\s+(?P<num>\d+[A-Z]?)[\.\s]+(?P<title>[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^.\n\r]*?)(?=\n|$))"
        for match in re.finditer(pattern1, text, re.IGNORECASE):
            markers.append({
                'type': 'lesson',
                'position': match.start(),
                'number': int(re.search(r'\d+', match.group('num')).group()),
                'title': match.group('title').strip(),
                'full_match': match.group('full'),
                'pattern': 'uppercase_dot'
            })

        # Pattern 2: "BÀI X: TITLE" (uppercase, with colon) - sgk_tin_hoc_6
        pattern2 = r"(?P<full>(?:BÀI|BÃ€I)\s+(?P<num>\d+[A-Z]?):\s*(?P<title>[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^:\n\r]*?)(?=\n|$))"
        for match in re.finditer(pattern2, text, re.IGNORECASE):
            markers.append({
                'type': 'lesson',
                'position': match.start(),
                'number': int(re.search(r'\d+', match.group('num')).group()),
                'title': match.group('title').strip(),
                'full_match': match.group('full'),
                'pattern': 'uppercase_colon'
            })

        # Pattern 3: "Bài X. Title" (mixed case, with dot) - sgk_tin_hoc_10, 11, 12
        pattern3 = r"(?P<full>Bài\s+(?P<num>\d+[A-Z]?)[\.\s]+(?P<title>[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^.\n\r]*?)(?=\n|$))"
        for match in re.finditer(pattern3, text):
            markers.append({
                'type': 'lesson',
                'position': match.start(),
                'number': int(re.search(r'\d+', match.group('num')).group()),
                'title': match.group('title').strip(),
                'full_match': match.group('full'),
                'pattern': 'mixed_case_dot'
            })

        # Pattern 4: "* Bài X. Title" (with bullet point) - sgk_tin_hoc_3
        pattern4 = r"(?P<full>\*\s*Bài\s+(?P<num>\d+[A-Z]?)[\.\s]+(?P<title>[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^,\n\r]*?)(?:,|\n|$))"
        for match in re.finditer(pattern4, text):
            markers.append({
                'type': 'lesson',
                'position': match.start(),
                'number': int(re.search(r'\d+', match.group('num')).group()),
                'title': match.group('title').strip(),
                'full_match': match.group('full'),
                'pattern': 'bullet_point'
            })

        # Pattern 5: "BÀI X" (standalone, uppercase) - sgk_tin_hoc_10, 11, 12
        pattern5 = r"(?P<full>^(?:BÀI|BÃ€I)\s+(?P<num>\d+[A-Z]?)(?:\s*$|\s+(?P<title>[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^\n\r]*?))?$)"
        for match in re.finditer(pattern5, text, re.MULTILINE):
            markers.append({
                'type': 'lesson',
                'position': match.start(),
                'number': int(re.search(r'\d+', match.group('num')).group()),
                'title': match.group('title').strip() if match.group('title') else '',
                'full_match': match.group('full'),
                'pattern': 'standalone_uppercase'
            })

        # Pattern 6: "BÀI X. TITLE" (plain text, no markdown) - sgk_tin_hoc_5
        pattern6 = r"(?P<full>^(?:BÀI|BÃ€I)\s+(?P<num>\d+[A-Z]?)[\.\s]+(?P<title>[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^.\n\r]*?)(?=\n|$))"
        for match in re.finditer(pattern6, text, re.MULTILINE):
            markers.append({
                'type': 'lesson',
                'position': match.start(),
                'number': int(re.search(r'\d+', match.group('num')).group()),
                'title': match.group('title').strip(),
                'full_match': match.group('full'),
                'pattern': 'plain_text_dot'
            })

        # Pattern 7: Table of contents format "Bài X. Title (Trang Y)" - all files
        pattern7 = r"(?P<full>Bài\s+(?P<num>\d+[A-Z]?)[\.\s]+(?P<title>[^(\n\r]*?)\s*\((?:Trang|trang)\s+\d+\))"
        for match in re.finditer(pattern7, text):
            markers.append({
                'type': 'lesson',
                'position': match.start(),
                'number': int(re.search(r'\d+', match.group('num')).group()),
                'title': match.group('title').strip(),
                'full_match': match.group('full'),
                'pattern': 'table_of_contents'
            })

        # Pattern 8: "BÀI X TITLE" (no punctuation after number) - sgk_tin_hoc_4
        pattern8 = r"(?P<full>^(?:BÀI|BÃ€I)\s+(?P<num>\d+[A-Z]?)\s+(?P<title>[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĐỨ][^\n\r]*?)(?=\n|$))"
        for match in re.finditer(pattern8, text, re.MULTILINE):
            # Skip if this looks like it already has punctuation (caught by other patterns)
            if re.search(r'[\.\:\-]', match.group('full')):
                continue
            markers.append({
                'type': 'lesson',
                'position': match.start(),
                'number': int(re.search(r'\d+', match.group('num')).group()),
                'title': match.group('title').strip(),
                'full_match': match.group('full'),
                'pattern': 'no_punctuation'
            })

        # Enhanced deduplication logic
        unique_markers = {}
        for marker in markers:
            # Extract lesson variant (A, B, etc.) if present
            variant = ''
            if re.search(r'\d+[A-Z]', marker['full_match']):
                variant = re.search(r'\d+([A-Z])', marker['full_match']).group(1)
            
            # Create composite key including variant
            key = (marker['number'], variant)
            
            # Skip table of contents entries if we have actual lesson content
            if marker['pattern'] == 'table_of_contents':
                # Only keep TOC if no other pattern exists for this lesson
                if key not in unique_markers:
                    unique_markers[key] = marker
            else:
                # For non-TOC entries, prefer longer titles and actual content
                if key not in unique_markers:
                    unique_markers[key] = marker
                else:
                    existing = unique_markers[key]
                    # Prefer non-TOC over TOC
                    if existing['pattern'] == 'table_of_contents':
                        unique_markers[key] = marker
                    # Among non-TOC, prefer longer titles
                    elif len(marker['title']) > len(existing['title']):
                        unique_markers[key] = marker
                    # Prefer mixed case over uppercase for readability
                    elif (len(marker['title']) == len(existing['title']) and 
                          marker['pattern'] in ['mixed_case_dot', 'bullet_point'] and
                          existing['pattern'] in ['uppercase_dot', 'uppercase_colon', 'plain_text_dot']):
                        unique_markers[key] = marker

        sorted_markers = sorted(unique_markers.values(), key=lambda x: x['position'])
        
        # Log detailed statistics
        logger.info(f"🔍 Found {len(sorted_markers)} unique lesson markers using {len(set(m['pattern'] for m in sorted_markers))} patterns")
        for pattern in set(m['pattern'] for m in sorted_markers):
            count = len([m for m in sorted_markers if m['pattern'] == pattern])
            logger.info(f"  📋 {pattern}: {count} lessons")
        
        # Log lesson numbers found
        lesson_numbers = sorted([m['number'] for m in sorted_markers])
        logger.info(f"📚 Lesson numbers detected: {lesson_numbers}")
        
        return sorted_markers

    def _find_chapter_markers(self, text: str) -> List[Dict]:
        """
        🔥 COMPREHENSIVE: Find all chapter markers with multiple patterns
        """
        markers = []
        
        # Pattern 1: "CHỦ ĐỀ X. TITLE" (uppercase)
        pattern1 = r"(?P<full>(?:CHỦ ĐỀ|CHá»¦ Äá»€)\s+(?P<num>\d+)[\.\s:：-]+(?P<title>[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^\n\r]*?)(?=\n|$))"
        for match in re.finditer(pattern1, text, re.IGNORECASE):
            markers.append({
                'type': 'chapter',
                'position': match.start(),
                'number': int(match.group('num')),
                'title': match.group('title').strip(),
                'full_match': match.group('full'),
                'pattern': 'chapter_uppercase'
            })

        # Pattern 2: "Chủ đề X. Title" (mixed case)
        pattern2 = r"(?P<full>Chủ đề\s+(?P<num>\d+)[\.\s:：-]+(?P<title>[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^\n\r]*?)(?=\n|$))"
        for match in re.finditer(pattern2, text):
            markers.append({
                'type': 'chapter',
                'position': match.start(),
                'number': int(match.group('num')),
                'title': match.group('title').strip(),
                'full_match': match.group('full'),
                'pattern': 'chapter_mixed_case'
            })

        # Pattern 3: "PHẦN X. TITLE" (part/section)
        pattern3 = r"(?P<full>PHẦN\s+(?P<num>\d+)[\.\s:：-]+(?P<title>[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^\n\r]*?)(?=\n|$))"
        for match in re.finditer(pattern3, text, re.IGNORECASE):
            markers.append({
                'type': 'part',
                'position': match.start(),
                'number': int(match.group('num')),
                'title': match.group('title').strip(),
                'full_match': match.group('full'),
                'pattern': 'part_uppercase'
            })

        return sorted(markers, key=lambda x: x['position'])

    def _find_section_markers(self, text: str) -> List[Dict]:
        """
        🔥 COMPREHENSIVE: Find all section markers within lessons
        """
        markers = []
        
        # Pattern 1: "1. Section title" (numbered sections)
        pattern1 = r"(?P<full>^(?P<num>\d+)[\.\s]+(?P<title>[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^\n\r]*?)(?=\n|$))"
        for match in re.finditer(pattern1, text, re.MULTILINE):
            markers.append({
                'type': 'section',
                'position': match.start(),
                'number': int(match.group('num')),
                'title': match.group('title').strip(),
                'full_match': match.group('full'),
                'pattern': 'numbered_section'
            })

        # Pattern 2: "a) Subsection" (lettered subsections)
        pattern2 = r"(?P<full>^(?P<letter>[a-z])\)\s+(?P<title>[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^\n\r]*?)(?=\n|$))"
        for match in re.finditer(pattern2, text, re.MULTILINE):
            markers.append({
                'type': 'subsection',
                'position': match.start(),
                'letter': match.group('letter'),
                'title': match.group('title').strip(),
                'full_match': match.group('full'),
                'pattern': 'lettered_subsection'
            })

        # Pattern 3: "- Activity:" or "• Activity:" (activity markers)
        pattern3 = r"(?P<full>^[-•]\s*(?P<title>(?:Hoạt động|Thực hành|Bài tập|Câu hỏi)[^\n\r]*?)(?=\n|$))"
        for match in re.finditer(pattern3, text, re.MULTILINE | re.IGNORECASE):
            markers.append({
                'type': 'activity',
                'position': match.start(),
                'title': match.group('title').strip(),
                'full_match': match.group('full'),
                'pattern': 'activity_marker'
            })

        return sorted(markers, key=lambda x: x['position'])

    def _split_into_lessons(self, text: str) -> List[str]:
        """
        🔥 ENHANCED: Split text into lessons using comprehensive marker detection
        """
        markers = self._find_lesson_markers(text)
        
        if not markers:
            logger.warning("⚠️ No lesson markers found, returning full text as single lesson")
            return [text]

        lessons = []
        chapter_buffer = ""

        for i, marker in enumerate(markers):
            # Get lesson content
            start_pos = marker['position']
            end_pos = markers[i + 1]['position'] if i + 1 < len(markers) else len(text)
            
            lesson_content = text[start_pos:end_pos].strip()
            
            # More lenient filtering - only skip extremely short content
            if len(lesson_content) < 50:
                logger.debug(f"⏭️ Skipping very short lesson {marker['number']}: {len(lesson_content)} chars")
                continue
                
            # More specific exercise section detection
            is_exercise_section = bool(re.search(r"^BÀI TẬP\s*$|^BÀI NGHỈ\s*$", lesson_content, re.IGNORECASE | re.MULTILINE))
            if is_exercise_section:
                logger.debug(f"⏭️ Skipping exercise section for lesson {marker['number']}")
                continue

            # Skip table of contents - check if content contains multiple "Bài X" patterns
            bai_count = len(re.findall(r'Bài\s+\d+', lesson_content, re.IGNORECASE))
            if bai_count > 3:  # If more than 3 "Bài X" patterns, likely table of contents
                logger.debug(f"⏭️ Skipping table of contents (found {bai_count} lesson references)")
                continue

            # Remove table of contents from beginning of lesson content
            # Look for patterns like "Bài X. Title, Trang Y" at the start
            lesson_content = re.sub(r'^.*?(?=CHỦ ĐỀ|BÀI\s+\d+\s+[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĐỨ])', '', lesson_content, flags=re.DOTALL | re.IGNORECASE)
            lesson_content = lesson_content.strip()
            
            # Skip if content becomes too short after cleaning
            if len(lesson_content) < 100:
                logger.debug(f"⏭️ Skipping lesson after cleaning: too short")
                continue

            # Check if previous content contains chapter info
            prev_content = text[max(0, start_pos - 1000):start_pos]
            chapter_match = re.search(r"(CHỦ ĐỀ|CHá»¦ Äá»€|Chủ đề)\s+(\d+)[\.\ s:：-]+([^\n\r]+)", prev_content, re.IGNORECASE)
            
            if chapter_match and not chapter_buffer:
                chapter_info = chapter_match.group(0)
                # Only add chapter info, not the full table of contents
                chapter_buffer = chapter_info + "\n\n"

            # Add lesson content without table of contents
            lessons.append(lesson_content)
            
            # Log lesson info
            logger.info(f"  📖 Bài {marker['number']}: {marker['title'][:50]}{'...' if len(marker['title']) > 50 else ''}")
            logger.info(f"      └─ {marker['pattern']} pattern")
            logger.info(f"      └─ Length: {len(lesson_content)} chars")

        logger.info(f"✅ Total lessons extracted: {len(lessons)}")
        return lessons

    def _split_into_lessons_fallback(self, text: str) -> List[str]:
        """
        Fallback: Split text into lessons without aggressive filters.
        Ensures content is returned even when detection is noisy.
        """
        markers = self._find_lesson_markers(text)
        if not markers:
            logger.warning("⚠️ Fallback: no lesson markers found")
            return []

        lessons: List[str] = []
        for i, marker in enumerate(markers):
            start_pos = marker['position']
            end_pos = markers[i + 1]['position'] if i + 1 < len(markers) else len(text)
            lesson_content = text[start_pos:end_pos].strip()

            # Do not skip short content aggressively; only skip if extremely short
            if len(lesson_content) < 10:
                logger.debug(f"⏭️ Fallback: skipping extremely short lesson {marker['number']}: {len(lesson_content)} chars")
                continue

            lessons.append(lesson_content)
            logger.info(
                f"  📖 Fallback Bài {marker['number']}: {marker['title'][:50]}{'...' if len(marker['title']) > 50 else ''}"
                f" (len={len(lesson_content)} chars)"
            )

        logger.info(f"✅ Fallback total lessons extracted: {len(lessons)}")
        return lessons

    def _extract_lesson_metadata(
        self,
        lesson_text: str,
        subject_info: Dict,
        grade: Optional[int],
        education_level: Optional[str]
    ) -> Dict:
        """
        🔥 ENHANCED: Extract comprehensive lesson metadata with improved patterns
        """
        metadata = {
            **subject_info,
            "grade": grade,
            "education_level": education_level,
        }

        # NOTE: Chapter info will be added from chapter_map in process_txt
        # Do NOT extract chapter from lesson text to avoid incorrect mapping

        # Enhanced lesson patterns for better detection
        lesson_patterns = [
            r"BÀI\s+(\d+[A-Z]?)[\.\ s:：-]+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^\n\r]+?)(?=\n|$)",
            r"BÃ€I\s+(\d+[A-Z]?)[\.\ s:：-]+([A-ZÀ-Ý][^\n\r]+?)(?=\n|$)",
            # Avoid matching table of contents by excluding patterns with "Trang"
            r"Bài\s+(\d+[A-Z]?)[\.\ s:：-]+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^,\n\r]*?)(?!\s*,\s*Trang)(?=\n|$)",
            r"\*\s*Bài\s+(\d+[A-Z]?)[\.\ s]+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^,\n\r]*)",
            r"Bài\s+(\d+[A-Z]?)[\.\ s]+([^(\n\r]*?)\s*\((?:Trang|trang)\s+\d+\)",
            # Pattern for "BÀI X TITLE" (no punctuation) - sgk_tin_hoc_4
            # This pattern can match anywhere in the line, not just at the start
            r"BÀI\s+(\d+)\s+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĐỨ][^\n]+?)(?=\s+Sau\s+bài|(?=\n)|$)",
            r"BÃ€I\s+(\d+)\s+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĐỨ][^\n]+?)(?=\s+Sau\s+bài|(?=\n)|$)"
        ]

        for pattern in lesson_patterns:
            lesson_match = re.search(pattern, lesson_text, re.IGNORECASE | re.MULTILINE)
            if lesson_match:
                lesson_num_str = lesson_match.group(1)
                lesson_num = int(re.search(r'\d+', lesson_num_str).group())
                lesson_title = re.sub(r'\s+\d+\s*$', '', lesson_match.group(2).strip())
                lesson_title = re.sub(r'\s+', ' ', lesson_title).strip()
                
                # Clean up lesson title - remove everything after "Sau bài này em sẽ"
                lesson_title = re.sub(r'\s+Sau\s+bài\s+này.*$', '', lesson_title, flags=re.IGNORECASE | re.DOTALL)
                lesson_title = lesson_title.strip()
                
                metadata["lesson_number"] = lesson_num
                metadata["lesson_title"] = lesson_title
                break

        # Enhanced metadata extraction
        metadata["topics"] = self._extract_learning_objectives(lesson_text)
        metadata["sections"] = self._extract_sections(lesson_text)
        
        # Enhanced detection patterns
        metadata["has_questions"] = bool(re.search(r"(?:Câu hỏi|Hỏi|Thảo luận)\s*\d*[:：]?", lesson_text, re.IGNORECASE))
        metadata["has_activities"] = bool(re.search(r"(?:HOẠT ĐỘNG|Hoạt động|Thực hành|Làm việc)\s*\d*[:：]?", lesson_text, re.IGNORECASE))
        metadata["has_exercises"] = bool(re.search(r"(?:LUYỆN TẬP|VẬN DỤNG|BÀI TẬP|Bài tập|Thực hiện)", lesson_text, re.IGNORECASE))
        metadata["has_code"] = any(kw in lesson_text for kw in ["def ", "class ", "print(", "import ", "```"]) or bool(re.search(r"\bcode\b|\bScript\b", lesson_text, re.IGNORECASE))
        metadata["has_formula"] = any(op in lesson_text for op in ["=", "+", "-", "×", "÷", "√"])
        metadata["has_diagram"] = any(k in lesson_text.lower() for k in ["hình", "sơ đồ", "biểu đồ", "đồ thị"])
        metadata["code_blocks_count"] = lesson_text.count("```")
        metadata["question_count"] = len(re.findall(r"(?:Câu hỏi|Hỏi)\s*\d+[:：]?", lesson_text, re.IGNORECASE))
        metadata["activity_count"] = len(re.findall(r"(?:HOẠT ĐỘNG|Hoạt động)\s*\d+[:：]?", lesson_text, re.IGNORECASE))
        
        # Additional metadata
        metadata["content_length"] = len(lesson_text)
        metadata["estimated_reading_time"] = max(1, len(lesson_text) // 200)  # Rough estimate in minutes

        return metadata

    def _extract_learning_objectives(self, text: str) -> List[str]:
        """Extract learning objectives"""
        objectives = []
        goal_section = re.search(
            r"Sau bài (?:này )?em (?:sẽ|cần):\s*([\s\S]*?)(?=\n\n[A-Z]|\nKHỞI ĐỘNG|\nNỘI DUNG|$)",
            text,
            re.IGNORECASE
        )

        if goal_section:
            goal_text = goal_section.group(1)
            for line in goal_text.split('\n'):
                line = line.strip()
                if line.startswith(('*', '-', '•')):
                    clean = re.sub(r'^[\*\-•]\s*', '', line).strip()
                    if 10 <= len(clean) <= 200:
                        objectives.append(clean)

        return objectives[:10]

    def _extract_sections(self, text: str) -> List[Dict[str, str]]:
        """Extract sections"""
        return []

    def _smart_chunk_by_sections(self, text: str, metadata: Dict) -> List[Dict]:
        """Chunk by sections"""
        return self._basic_chunk(text, metadata)

    def _basic_chunk(self, text: str, metadata: Dict) -> List[Dict]:
        """Basic chunking"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
        )

        chunks = []
        for chunk_text in splitter.split_text(text):
            chunk = {
                'content': chunk_text,
                'metadata': metadata.copy(),
                'token_count': self._count_tokens(chunk_text)
            }
            chunks.append(chunk)

        return chunks

    def _detect_subject(self, filename: str, text: str = "") -> Dict:
        """Detect subject"""
        name = filename.lower()
        if "tin" in name or "tin học" in text.lower():
            return {"subject": "Tin học", "subject_key": "tin_hoc"}
        elif "toan" in name or "toán" in text.lower():
            return {"subject": "Toán học", "subject_key": "toan"}
        elif "van" in name or "ngữ văn" in text.lower():
            return {"subject": "Ngữ văn", "subject_key": "ngu_van"}
        return {"subject": "Unknown", "subject_key": "unknown"}

    def _detect_grade(self, filename: str) -> Tuple[Optional[int], Optional[str]]:
        """Detect grade"""
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
        """Count tokens"""
        return len(self.encoding.encode(text))

    def _save_chunks(self, chunks: List[Dict], output_file: Path):
        """Save chunks to JSON"""
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="📘 Process textbook files into JSON chunks")
    parser.add_argument("--input", required=True, help="Input TXT file path")
    parser.add_argument("--output", required=True, help="Output folder")
    parser.add_argument("--type", choices=["txt", "pdf"], default="txt", help="File type")
    parser.add_argument("--subject", default=None, help="Subject (tin_hoc, toan, etc.)")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Chunk overlap")
    parser.add_argument("--no-smart-chunking", action="store_true", help="Disable smart chunking")

    args = parser.parse_args()

    processor = DocumentProcessor(
        subject=args.subject,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        smart_chunking=not args.no_smart_chunking
    )

    path = Path(args.input)

    if args.type == "txt":
        if path.is_dir():
            for txt_file in path.glob("*.txt"):
                processor.process_txt(txt_file, args.output)
        else:
            processor.process_txt(path, args.output)
    elif args.type == "pdf":
        logger.error("PDF processing not implemented yet. Please use TXT files.")
        return


if __name__ == "__main__":
    main()