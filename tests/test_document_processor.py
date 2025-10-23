"""Unit tests for DocumentProcessor"""

import pytest
from src.sgk_rag.core.document_processor import DocumentProcessor


class TestDocumentProcessor:
    """Test DocumentProcessor class"""

    @pytest.fixture
    def processor(self):
        """Create processor instance"""
        return DocumentProcessor(chunk_size=500, chunk_overlap=100)

    def test_detect_grade(self, processor):
        """Test grade detection from filename"""
        # Test cases
        cases = [
            ("sgk_tin_hoc_lop_3.pdf", 3, "Tiểu học"),
            ("tin_hoc_10.pdf", 10, "THPT"),
            ("SGK_Lop6_TinHoc.pdf", 6, "THCS"),
        ]

        for filename, expected_grade, expected_level in cases:
            grade, level = processor._detect_grade(filename)
            assert grade == expected_grade
            assert level == expected_level

    def test_roman_to_int(self, processor):
        """Test Roman numeral conversion"""
        cases = [
            ("I", 1),
            ("IV", 4),
            ("IX", 9),
            ("X", 10),
        ]

        for roman, expected in cases:
            result = processor._roman_to_int(roman)
            assert result == expected

    def test_extract_topics(self, processor):
        """Test topic extraction"""
        text = "Thuật toán là một dãy hữu hạn các bước. Lập trình Python rất dễ học."
        topics = processor._extract_topics(text, subject_key="tin_hoc", education_level="THCS")

        assert "thuật toán" in topics
        assert "lập trình" in topics
        assert "python" in topics

    def test_detect_code(self, processor):
        """Test code detection"""
        text_with_code = "def hello():\n    print('Hello')"
        text_without_code = "Đây là văn bản thông thường"

        assert processor._detect_code(text_with_code) is True
        assert processor._detect_code(text_without_code) is False
