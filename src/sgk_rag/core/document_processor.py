"""
Enhanced Document Processor with Better Metadata Extraction
Optimized for Vietnamese textbooks (especially Tin học)
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
        self.subject_key = subject
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
        self.smart_chunking = smart_chunking
        logger.info(f"DocumentProcessor initialized (subject={subject or 'auto'}, smart_chunking={smart_chunking})")

    def process_txt(self, txt_path: str | Path, output_dir: Optional[str | Path] = None) -> List[Dict]:
        """Process a single TXT file with enhanced metadata extraction"""
        txt_path = Path(txt_path)
        logger.info(f"📄 Processing TXT: {txt_path.name}")

        if not txt_path.exists():
            raise FileNotFoundError(f"TXT not found: {txt_path}")

        with open(txt_path, "r", encoding="utf-8") as f:
            full_text = f.read().strip()

        if not full_text:
            logger.warning(f"⚠️ Empty file: {txt_path.name}")
            return []

        # Detect subject & grade trước
        subject_info = self._detect_subject(txt_path.name, full_text)
        grade, education_level = self._detect_grade(txt_path.name)

        # Loại bỏ phần đầu sách (lời nói đầu, hướng dẫn sử dụng)
        full_text = self._remove_intro_sections(full_text)

        # Loại bỏ mục lục
        full_text = self._remove_table_of_contents(full_text)

        # Clean up text
        full_text = self._preprocess_text(full_text)

        # Split thành các bài học riêng biệt
        lessons = self._split_into_lessons(full_text)
        logger.info(f"🧩 Detected {len(lessons)} lessons")

        all_chunks = []
        chunk_id = 0

        # 🔥 Biến để "nhớ" chủ đề hiện tại
        current_chapter = None
        current_chapter_number = None
        current_chapter_title = None

        for lesson_text in lessons:
            # Extract metadata cho từng bài
            metadata = self._extract_lesson_metadata(lesson_text, subject_info, grade, education_level)

            # 🔥 Nếu bài này có chủ đề mới, cập nhật current_chapter
            if metadata.get('chapter'):
                current_chapter = metadata['chapter']
                current_chapter_number = metadata.get('chapter_number')
                current_chapter_title = metadata.get('chapter_title')
            # 🔥 Nếu không có, dùng chủ đề trước đó
            else:
                metadata['chapter'] = current_chapter
                metadata['chapter_number'] = current_chapter_number
                metadata['chapter_title'] = current_chapter_title

            logger.info(f"  📚 {metadata.get('chapter') or 'N/A'} | "
                       f"Bài {metadata.get('lesson_number')}: {metadata.get('lesson_title') or 'N/A'}")

            # Chunk bài học theo sections nếu có
            if self.smart_chunking and metadata.get('sections'):
                chunks = self._smart_chunk_by_sections(lesson_text, metadata)
            else:
                chunks = self._basic_chunk(lesson_text, metadata)

            # Gán chunk_id
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
        """Loại bỏ phần hướng dẫn sử dụng sách, lời nói đầu"""
        patterns = [
            r"HƯỚNG DẪN SỬ DỤNG SÁCH[\s\S]*?(?=CHỦ ĐỀ|MỤC LỤC)",
            r"LỜI NÓI ĐẦU[\s\S]*?(?=CHỦ ĐỀ|MỤC LỤC)",
        ]
        for pattern in patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        return text

    def _remove_table_of_contents(self, text: str) -> str:
        """Loại bỏ mục lục - từ 'MỤC LỤC' đến trước 'CHỦ ĐỀ' đầu tiên"""
        # Tìm phần MỤC LỤC và bỏ đi cho đến CHỦ ĐỀ đầu tiên
        toc_pattern = r"MỤC LỤC[\s\S]*?(?=CHỦ ĐỀ\s+\d+\.)"
        text = re.sub(toc_pattern, "", text, flags=re.IGNORECASE)
        return text

    def _preprocess_text(self, text: str) -> str:
        """Clean up text"""
        # Bỏ page numbers
        text = re.sub(r"(?:TRANG|Trang|Page)\s+\d+", "", text, flags=re.IGNORECASE)
        # Bỏ dấu gạch ngang phân trang
        text = re.sub(r"^[-=_]{3,}$", "", text, flags=re.MULTILINE)
        # Normalize whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()

    def _split_into_lessons(self, text: str) -> List[str]:
        """
        Split text thành các bài học riêng biệt
        Mỗi bài bắt đầu bằng 'BÀI <số>:'
        """
        # Pattern để tìm đầu mỗi bài: "BÀI 1:", "BÀI 2:", etc.
        lesson_pattern = r"(?=BÀI\s+\d+[:：])"

        parts = re.split(lesson_pattern, text, flags=re.IGNORECASE)

        # Lọc bỏ đoạn rỗng hoặc quá ngắn
        lessons = [p.strip() for p in parts if len(p.strip()) > 200]

        return lessons

    def _extract_lesson_metadata(
        self,
        lesson_text: str,
        subject_info: Dict,
        grade: Optional[int],
        education_level: Optional[str]
    ) -> Dict:
        """Extract đầy đủ metadata từ một bài học"""

        metadata = {
            **subject_info,
            "grade": grade,
            "education_level": education_level,
        }

        # 1. Detect Chủ đề (chapter)
        chapter_match = re.search(
            r"(CHỦ ĐỀ|CHU DE)\s+(\d+)[\.\s:：-]*([^\n\r]+)",
            lesson_text,
            re.IGNORECASE
        )
        if chapter_match:
            chapter_num = int(chapter_match.group(2))
            chapter_title = re.sub(r'\s+', ' ', chapter_match.group(3).strip()).title()
            metadata["chapter_number"] = chapter_num
            metadata["chapter_title"] = chapter_title
            metadata["chapter"] = f"Chủ đề {chapter_num}. {chapter_title}"

        # 2. Detect Bài học (lesson)
        lesson_match = re.search(
            r"BÀI\s+(\d+)[:：\.\s-]*([^\n\r]+)",
            lesson_text,
            re.IGNORECASE
        )
        if lesson_match:
            lesson_num = int(lesson_match.group(1))
            lesson_title = re.sub(r'\s+', ' ', lesson_match.group(2).strip()).title()
            metadata["lesson_number"] = lesson_num
            metadata["lesson_title"] = lesson_title

        # 3. Detect mục tiêu học tập (topics/learning objectives)
        metadata["topics"] = self._extract_learning_objectives(lesson_text)

        # 4. Detect sections (Hoạt động, phần nội dung)
        metadata["sections"] = self._extract_sections(lesson_text)

        # 5. Detect content types
        metadata["has_questions"] = bool(re.search(r"Câu hỏi\s*\d*[:：]?", lesson_text, re.IGNORECASE))
        metadata["has_activities"] = bool(re.search(r"HOẠT ĐỘNG\s*\d*[:：]?", lesson_text, re.IGNORECASE))
        metadata["has_exercises"] = bool(re.search(r"LUYỆN TẬP|VẬN DỤNG", lesson_text, re.IGNORECASE))
        metadata["has_code"] = any(kw in lesson_text for kw in ["def ", "class ", "print(", "import ", "```"])
        metadata["has_formula"] = any(op in lesson_text for op in ["=", "+", "-", "×", "÷", "√"])
        metadata["has_diagram"] = any(k in lesson_text.lower() for k in ["hình", "sơ đồ", "biểu đồ", "đồ thị"])

        # 6. Count special blocks
        metadata["code_blocks_count"] = lesson_text.count("```")
        metadata["question_count"] = len(re.findall(r"Câu hỏi\s*\d+[:：]?", lesson_text, re.IGNORECASE))
        metadata["activity_count"] = len(re.findall(r"HOẠT ĐỘNG\s*\d+[:：]?", lesson_text, re.IGNORECASE))

        return metadata

    def _extract_learning_objectives(self, text: str) -> List[str]:
        """Extract mục tiêu học tập từ phần 'Sau bài này em sẽ:'"""
        objectives = []

        # Tìm phần mục tiêu
        goal_section = re.search(
            r"Sau bài (?:này )?em (?:sẽ|cần):\s*([\s\S]*?)(?=\n\n[A-Z]|\nKHỞI ĐỘNG|\nNỘI DUNG|$)",
            text,
            re.IGNORECASE
        )

        if goal_section:
            goal_text = goal_section.group(1)
            # Tìm các dòng bắt đầu bằng * hoặc -
            for line in goal_text.split('\n'):
                line = line.strip()
                if line.startswith(('*', '-', '•')):
                    clean = re.sub(r'^[\*\-•]\s*', '', line).strip()
                    if 10 <= len(clean) <= 200:
                        objectives.append(clean)

        return objectives[:10]  # Giới hạn 10 objectives

    def _extract_sections(self, text: str) -> List[Dict[str, str]]:
        """
        Extract các sections (phần) trong bài học
        VD: KHỞI ĐỘNG, HOẠT ĐỘNG 1, NỘI DUNG, LUYỆN TẬP, VẬN DỤNG
        """
        sections = []

        # Patterns cho các sections phổ biến
        section_patterns = [
            r"(KHỞI ĐỘNG)(?:\s*[:：])?\s*([^\n]*)",
            r"(HOẠT ĐỘNG)\s*(\d+)[:：]?\s*([^\n]+)",
            r"(LUYỆN TẬP)(?:\s*[:：])?\s*([^\n]*)",
            r"(VẬN DỤNG)(?:\s*[:：])?\s*([^\n]*)",
            r"(\d+)\.\s+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝ][^:\n]{5,80})",  # Numbered sections
        ]

        for pattern in section_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                if len(match.groups()) == 2:
                    section_type = match.group(1).strip()
                    section_title = match.group(2).strip() if match.group(2) else ""
                elif len(match.groups()) == 3:
                    section_type = f"{match.group(1)} {match.group(2)}"
                    section_title = match.group(3).strip()
                else:
                    continue

                sections.append({
                    "type": section_type,
                    "title": section_title,
                    "position": match.start()
                })

        # Sort by position
        sections.sort(key=lambda x: x['position'])

        # Remove position before returning
        for s in sections:
            del s['position']

        return sections

    def _smart_chunk_by_sections(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Chunk bài học dựa trên sections
        Mỗi chunk là một section hoặc một phần của section nếu quá dài
        """
        chunks = []
        sections = metadata.get('sections', [])

        if not sections:
            return self._basic_chunk(text, metadata)

        # Tìm vị trí của các sections trong text
        section_positions = []
        for section in sections:
            section_marker = f"{section['type']}"
            if section['title']:
                section_marker += f": {section['title']}"

            pos = text.find(section_marker)
            if pos != -1:
                section_positions.append((pos, section))

        section_positions.sort(key=lambda x: x[0])

        # Extract text cho từng section
        for i, (pos, section) in enumerate(section_positions):
            next_pos = section_positions[i+1][0] if i+1 < len(section_positions) else len(text)
            section_text = text[pos:next_pos].strip()

            # Nếu section quá dài, chia nhỏ
            if len(section_text) > self.chunk_size * 1.5:
                sub_chunks = self._basic_chunk(section_text, metadata)
                for sub_chunk in sub_chunks:
                    sub_chunk['section_type'] = section['type']
                    sub_chunk['section_title'] = section.get('title', '')
                    chunks.append(sub_chunk)
            else:
                chunk = {
                    'content': section_text,
                    'metadata': metadata.copy(),
                    'token_count': self._count_tokens(section_text),
                    'section_type': section['type'],
                    'section_title': section.get('title', '')
                }
                chunks.append(chunk)

        return chunks

    def _basic_chunk(self, text: str, metadata: Dict) -> List[Dict]:
        """Chunk cơ bản sử dụng RecursiveCharacterTextSplitter"""
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
        """Detect subject from filename or content"""
        name = filename.lower()

        if "tin" in name or "tin học" in text.lower():
            return {"subject": "Tin học", "subject_key": "tin_hoc"}
        elif "toan" in name or "toán" in text.lower():
            return {"subject": "Toán học", "subject_key": "toan"}
        elif "van" in name or "ngữ văn" in text.lower():
            return {"subject": "Ngữ văn", "subject_key": "ngu_van"}

        return {"subject": "Unknown", "subject_key": "unknown"}

    def _detect_grade(self, filename: str) -> Tuple[Optional[int], Optional[str]]:
        """Detect grade level from filename"""
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
        """Save chunks to JSON file"""
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="📘 Process textbook files into JSON chunks")
    parser.add_argument("--input", required=True, help="Input TXT file path")
    parser.add_argument("--output", required=True, help="Output folder")
    parser.add_argument("--type", choices=["txt", "pdf"], default="txt", help="File type (txt or pdf)")
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