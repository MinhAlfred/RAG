"""
Simple Document Processor - Đọc toàn bộ nội dung và chia chunk theo kích thước cố định
Không lọc/bỏ qua nội dung, chỉ thêm metadata nhẹ nhàng
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


class SimpleDocumentProcessor:
    """
    Simple Document Processor - Đọc toàn bộ nội dung, không lọc
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        encoding_name: str = "cl100k_base"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self._count_tokens,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def process_txt(self, txt_path: str | Path, output_dir: Optional[str | Path] = None) -> List[Dict]:
        """
        Process TXT file - đọc toàn bộ nội dung và chia chunk
        """
        txt_path = Path(txt_path)
        logger.info(f"📄 Processing TXT: {txt_path.name}")
        
        if not txt_path.exists():
            raise FileNotFoundError(f"TXT not found: {txt_path}")
        
        # Đọc toàn bộ file
        try:
            with open(txt_path, "r", encoding="utf-8", errors='replace') as f:
                full_text = f.read().strip()
            logger.info(f"✅ Successfully read file: {len(full_text)} characters")
        except Exception as e:
            logger.error(f"❌ Could not read file: {e}")
            return []
        
        if not full_text:
            logger.error("❌ Empty file content")
            return []
        
        # Detect subject & grade
        subject_info = self._detect_subject(txt_path.name, full_text)
        grade, education_level = self._detect_grade(txt_path.name)
        
        # Basic text cleanup - chỉ loại bỏ whitespace thừa
        full_text = self._basic_cleanup(full_text)
        
        # Chia thành chunks theo kích thước cố định
        text_chunks = self.text_splitter.split_text(full_text)
        logger.info(f"🧩 Split into {len(text_chunks)} chunks")
        
        # Tạo chunks với metadata
        all_chunks = []
        for i, chunk_text in enumerate(text_chunks):
            # Extract metadata nhẹ nhàng từ chunk content
            metadata = self._extract_chunk_metadata(
                chunk_text, subject_info, grade, education_level, i
            )
            
            chunk = {
                'chunk_id': f"{txt_path.stem}_{i:04d}",
                'content': chunk_text,
                'token_count': self._count_tokens(chunk_text),
                'source_file': txt_path.name,
                'metadata': metadata
            }
            all_chunks.append(chunk)
        
        avg_tokens = sum(c['token_count'] for c in all_chunks) // len(all_chunks) if all_chunks else 0
        logger.info(f"✅ Created {len(all_chunks)} chunks (avg {avg_tokens} tokens/chunk)")
        
        # Save chunks
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{txt_path.stem}_chunks.json"
            self._save_chunks(all_chunks, output_file)
        
        return all_chunks
    
    def _basic_cleanup(self, text: str) -> str:
        """
        Basic text cleanup - chỉ loại bỏ whitespace thừa
        """
        # Loại bỏ multiple whitespace
        text = re.sub(r'\s+', ' ', text)
        # Loại bỏ multiple newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        return text.strip()
    
    def _extract_chunk_metadata(
        self, 
        chunk_text: str, 
        subject_info: Dict, 
        grade: Optional[int], 
        education_level: Optional[str],
        chunk_index: int
    ) -> Dict:
        """
        Extract metadata nhẹ nhàng từ chunk content
        """
        metadata = {
            'subject': subject_info.get('subject'),
            'subject_key': subject_info.get('subject_key'),
            'grade': grade,
            'education_level': education_level,
            'chunk_index': chunk_index,
            'lesson_number': None,
            'lesson_title': None,
            'chapter': None,
            'chapter_number': None,
            'chapter_title': None,
            'topics': [],
            'has_code': False,
            'has_formula': False,
            'has_table': False
        }
        
        # Tìm lesson number và title trong chunk (nếu có)
        lesson_match = re.search(
            r'(?:BÀI|Bài)\s+(\d+)[\.:\s]*([^,\n\r\*\.\d]+?)(?:\s*,|\s*\*|\s*\n|\s*$)', 
            chunk_text, 
            re.IGNORECASE
        )
        if lesson_match:
            metadata['lesson_number'] = int(lesson_match.group(1))
            title = lesson_match.group(2).strip()
            # Loại bỏ các ký tự không mong muốn ở cuối
            title = re.sub(r'[,\*\.\s]+$', '', title)
            metadata['lesson_title'] = title
        
        # Tìm chapter trong chunk (nếu có)
        chapter_match = re.search(
            r'(?:CHỦ ĐỀ|Chủ đề)\s+(\d+)[\.:\s]*([^,\n\r\*\.\d]+?)(?:\s*,|\s*\*|\s*\n|\s*$)', 
            chunk_text, 
            re.IGNORECASE
        )
        if chapter_match:
            metadata['chapter_number'] = int(chapter_match.group(1))
            title = chapter_match.group(2).strip()
            # Loại bỏ các ký tự không mong muốn ở cuối
            title = re.sub(r'[,\*\.\s]+$', '', title)
            metadata['chapter_title'] = title
            metadata['chapter'] = f"Chủ đề {metadata['chapter_number']}. {metadata['chapter_title']}"
        
        # Detect content features
        metadata['has_code'] = bool(re.search(r'```|<code>|def |class |import |#include', chunk_text))
        metadata['has_formula'] = bool(re.search(r'\$.*\$|\\[a-zA-Z]+|∑|∫|√', chunk_text))
        metadata['has_table'] = bool(re.search(r'\|.*\|.*\||┌|├|└', chunk_text))
        
        # Extract simple topics (từ khóa quan trọng)
        topics = []
        topic_patterns = [
            r'máy tính', r'phần mềm', r'phần cứng', r'internet', r'web',
            r'lập trình', r'thuật toán', r'dữ liệu', r'thông tin', r'mạng',
            r'an toàn', r'bảo mật', r'virus', r'email', r'tìm kiếm'
        ]
        
        for pattern in topic_patterns:
            if re.search(pattern, chunk_text, re.IGNORECASE):
                topics.append(pattern)
        
        metadata['topics'] = topics[:5]  # Giới hạn 5 topics
        
        return metadata
    
    def _detect_subject(self, filename: str, text: str = "") -> Dict:
        """Detect subject from filename"""
        filename_lower = filename.lower()
        
        if 'tin_hoc' in filename_lower or 'tin học' in filename_lower:
            return {'subject': 'Tin học', 'subject_key': 'tin_hoc'}
        elif 'toan' in filename_lower or 'toán' in filename_lower:
            return {'subject': 'Toán', 'subject_key': 'toan'}
        elif 'ly' in filename_lower or 'lý' in filename_lower:
            return {'subject': 'Vật lý', 'subject_key': 'vat_ly'}
        elif 'hoa' in filename_lower or 'hóa' in filename_lower:
            return {'subject': 'Hóa học', 'subject_key': 'hoa_hoc'}
        else:
            return {'subject': 'Unknown', 'subject_key': 'unknown'}
    
    def _detect_grade(self, filename: str) -> Tuple[Optional[int], Optional[str]]:
        """Detect grade from filename"""
        grade_match = re.search(r'(\d+)', filename)
        if grade_match:
            grade = int(grade_match.group(1))
            if grade <= 5:
                return grade, 'Tiểu học'
            elif grade <= 9:
                return grade, 'Trung học cơ sở'
            elif grade <= 12:
                return grade, 'Trung học phổ thông'
        return None, None
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken"""
        return len(self.encoding.encode(text))
    
    def _save_chunks(self, chunks: List[Dict], output_file: Path):
        """Save chunks to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Saved {len(chunks)} chunks to {output_file}")


def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Document Processor")
    parser.add_argument("input_file", help="Input TXT file path")
    parser.add_argument("--output-dir", default="data/processed", help="Output directory")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size in tokens")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Chunk overlap in tokens")
    
    args = parser.parse_args()
    
    processor = SimpleDocumentProcessor(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    
    chunks = processor.process_txt(args.input_file, args.output_dir)
    print(f"✅ Processed {len(chunks)} chunks")


if __name__ == "__main__":
    main()