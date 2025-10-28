"""Slide Generator - Tạo nội dung slide từ SGK Informatics"""

import json
import time
from typing import List, Dict, Optional, Any
from pathlib import Path

from ..core.rag_pipeline import RAGPipeline
from ..models.dto import SlideContent, SlideRequest, SlideFormat


class SlideGenerator:
    """Class để tạo nội dung slide từ SGK"""
    
    def __init__(self, rag_pipeline: RAGPipeline):
        """
        Khởi tạo SlideGenerator
        
        Args:
            rag_pipeline: RAG pipeline đã được khởi tạo
        """
        self.rag_pipeline = rag_pipeline
        self.slide_templates = self._load_slide_templates()
    
    def _load_slide_templates(self) -> Dict[str, str]:
        """Load các template cho slide"""
        return {
            "title_slide": """# {title}
## Lớp {grade} - Tin học

---
""",
            "content_slide": """## {title}

{content}

{examples}

{notes}

---
""",
            "summary_slide": """## Tóm tắt

{summary}

### Điểm chính:
{key_points}

---
""",
            "exercise_slide": """## Bài tập

{exercises}

---
"""
        }
    
    def generate_slides(self, request: SlideRequest) -> List[SlideContent]:
        """
        Tạo slides từ topic
        
        Args:
            request: SlideRequest chứa thông tin yêu cầu
            
        Returns:
            List[SlideContent]: Danh sách slides đã tạo
        """
        slides = []
        
        # Slide 1: Title slide
        title_slide = self._create_title_slide(request.topic, request.grade)
        slides.append(title_slide)
        
        # Tạo outline cho các slide content
        outline = self._generate_outline(request.topic, request.slide_count - 1, request.grade)
        
        # Tạo content slides
        for i, section in enumerate(outline, 2):
            content_slide = self._create_content_slide(
                slide_number=i,
                section=section,
                topic=request.topic,
                grade=request.grade,
                include_examples=request.include_examples
            )
            slides.append(content_slide)
        
        # Thêm slide bài tập nếu được yêu cầu
        if request.include_exercises and len(slides) < request.slide_count:
            exercise_slide = self._create_exercise_slide(
                slide_number=len(slides) + 1,
                topic=request.topic,
                grade=request.grade
            )
            slides.append(exercise_slide)
        
        return slides[:request.slide_count]
    
    def _create_title_slide(self, topic: str, grade: Optional[int]) -> SlideContent:
        """Tạo slide tiêu đề"""
        grade_text = f"Lớp {grade}" if grade else "Tin học"
        
        content = f"""# {topic}
## {grade_text}

### Mục tiêu bài học:
- Hiểu được khái niệm cơ bản về {topic.lower()}
- Nắm được các thành phần và chức năng chính
- Áp dụng kiến thức vào thực tế

---"""
        
        return SlideContent(
            slide_number=1,
            title=topic,
            content=content,
            notes=f"Slide giới thiệu về chủ đề {topic}",
            sources=[]
        )
    
    def _generate_outline(self, topic: str, num_sections: int, grade: Optional[int]) -> List[str]:
        """Tạo outline cho các section của slide"""
        
        # Tạo câu hỏi để lấy thông tin về topic
        outline_question = f"""
        Hãy tạo một outline chi tiết cho bài giảng về "{topic}" gồm {num_sections} phần chính.
        Mỗi phần nên có tiêu đề rõ ràng và phù hợp với chương trình tin học lớp {grade if grade else 'trung học'}.
        Chỉ trả về danh sách các tiêu đề phần, mỗi tiêu đề trên một dòng.
        """
        
        try:
            response = self.rag_pipeline.query(
                outline_question, 
                grade_filter=grade, 
                return_sources=True
            )
            
            # Kiểm tra nếu response là dict (từ RAG pipeline)
            if isinstance(response, dict):
                response_text = response.get('answer', str(response))
            else:
                response_text = str(response)
            
            # Parse response để lấy các section
            lines = response_text.split('\n')
            sections = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and len(line) > 5:
                    # Loại bỏ số thứ tự và ký tự đặc biệt
                    clean_line = line.lstrip('0123456789.-* ').strip()
                    if clean_line and len(clean_line) > 3:
                        sections.append(clean_line)
            
            # Nếu không đủ sections, tạo thêm
            if len(sections) < num_sections:
                default_sections = [
                    "Khái niệm cơ bản",
                    "Thành phần chính",
                    "Chức năng và ứng dụng",
                    "Ví dụ thực tế",
                    "Tóm tắt và kết luận"
                ]
                
                for i in range(len(sections), num_sections):
                    if i < len(default_sections):
                        sections.append(default_sections[i])
                    else:
                        sections.append(f"Phần {i+1}")
            
            return sections[:num_sections]
            
        except Exception as e:
            print(f"Lỗi khi tạo outline: {e}")
            # Fallback outline
            return [
                "Khái niệm cơ bản",
                "Thành phần chính", 
                "Chức năng và ứng dụng",
                "Ví dụ thực tế"
            ][:num_sections]
    
    def _create_content_slide(self, slide_number: int, section: str, topic: str, 
                            grade: Optional[int], include_examples: bool) -> SlideContent:
        """Tạo slide nội dung"""
        
        # Tạo câu hỏi chi tiết cho section
        content_question = f"""
        Hãy giải thích chi tiết về "{section}" trong chủ đề "{topic}" 
        cho học sinh lớp {grade if grade else 'trung học'}.
        
        Yêu cầu:
        - Giải thích rõ ràng, dễ hiểu
        - Sử dụng thuật ngữ phù hợp với trình độ học sinh
        - Cung cấp thông tin chính xác từ sách giáo khoa
        {"- Bao gồm ví dụ cụ thể" if include_examples else ""}
        
        Chỉ trả về nội dung giải thích, không cần tiêu đề.
        """
        
        try:
            content_response = self.rag_pipeline.query(
                content_question,
                grade_filter=grade,
                return_sources=True
            )
            
            # Kiểm tra nếu response là dict
            if isinstance(content_response, dict):
                content_text = content_response.get('answer', str(content_response))
                # Lấy sources từ response
                response_sources = content_response.get('sources', [])
            else:
                content_text = str(content_response)
                response_sources = []
            
            # Tạo ví dụ nếu được yêu cầu
            examples = ""
            if include_examples:
                example_question = f"Cho ví dụ cụ thể về {section} trong {topic}"
                try:
                    example_response = self.rag_pipeline.query(
                        example_question,
                        grade_filter=grade,
                        return_sources=False
                    )
                    # Kiểm tra nếu response là dict
                    if isinstance(example_response, dict):
                        example_text = example_response.get('answer', str(example_response))
                    else:
                        example_text = str(example_response)
                    examples = f"\n### Ví dụ:\n{example_text[:200]}..."
                except:
                    examples = ""
            
            # Format content
            formatted_content = f"""## {section}

{content_text}

{examples}

---"""
            
            # Lấy sources từ response
            sources = []
            for source in response_sources:
                if isinstance(source, dict):
                    metadata = source.get('metadata', {})
                    lesson_title = metadata.get('lesson_title', 'Chưa xác định')
                    grade_info = metadata.get('grade', 'N/A')
                    sources.append(f"SGK Tin học Lớp {grade_info} - {lesson_title}")
                else:
                    sources.append(str(source))
            
            return SlideContent(
                slide_number=slide_number,
                title=section,
                content=formatted_content,
                notes=f"Slide về {section} trong chủ đề {topic}",
                sources=sources
            )
            
        except Exception as e:
            print(f"Lỗi khi tạo content slide: {e}")
            
            # Fallback content
            fallback_content = f"""## {section}

Nội dung về {section} trong {topic}.

(Đang cập nhật nội dung chi tiết...)

---"""
            
            return SlideContent(
                slide_number=slide_number,
                title=section,
                content=fallback_content,
                notes=f"Slide về {section}",
                sources=[]
            )
    
    def _create_exercise_slide(self, slide_number: int, topic: str, grade: Optional[int]) -> SlideContent:
        """Tạo slide bài tập"""
        
        exercise_question = f"""
        Tạo 3-5 câu hỏi bài tập về "{topic}" phù hợp với học sinh lớp {grade if grade else 'trung học'}.
        
        Yêu cầu:
        - Câu hỏi từ dễ đến khó
        - Bao gồm cả lý thuyết và thực hành
        - Phù hợp với nội dung sách giáo khoa
        
        Format: Mỗi câu hỏi trên một dòng, bắt đầu bằng số thứ tự.
        """
        
        try:
            exercise_response = self.rag_pipeline.query(
                exercise_question,
                grade_filter=grade,
                return_sources=False
            )
            
            # Kiểm tra nếu response là dict
            if isinstance(exercise_response, dict):
                exercise_text = exercise_response.get('answer', str(exercise_response))
            else:
                exercise_text = str(exercise_response)
            
            content = f"""## Bài tập

{exercise_text}

### Hướng dẫn:
- Thảo luận nhóm 5 phút
- Trình bày kết quả
- Giáo viên nhận xét và bổ sung

---"""
            
            return SlideContent(
                slide_number=slide_number,
                title="Bài tập",
                content=content,
                notes="Slide bài tập thực hành",
                sources=[]
            )
            
        except Exception as e:
            print(f"Lỗi khi tạo exercise slide: {e}")
            
            # Fallback exercises
            fallback_content = f"""## Bài tập

1. Nêu khái niệm cơ bản về {topic}?
2. Liệt kê các thành phần chính của {topic}?
3. Cho ví dụ ứng dụng của {topic} trong thực tế?

### Hướng dẫn:
- Thảo luận nhóm 5 phút
- Trình bày kết quả

---"""
            
            return SlideContent(
                slide_number=slide_number,
                title="Bài tập",
                content=fallback_content,
                notes="Slide bài tập",
                sources=[]
            )
    
    def format_slides(self, slides: List[SlideContent], format_type: SlideFormat) -> str:
        """
        Format slides theo định dạng yêu cầu
        
        Args:
            slides: Danh sách slides
            format_type: Định dạng output
            
        Returns:
            str: Nội dung slides đã format
        """
        if format_type == SlideFormat.MARKDOWN:
            return self._format_markdown(slides)
        elif format_type == SlideFormat.HTML:
            return self._format_html(slides)
        elif format_type == SlideFormat.POWERPOINT:
            return self._format_powerpoint(slides)
        else:  # TEXT
            return self._format_text(slides)
    
    def _format_markdown(self, slides: List[SlideContent]) -> str:
        """Format slides thành Markdown"""
        content = []
        for slide in slides:
            content.append(slide.content)
            if slide.notes:
                content.append(f"\n<!-- Notes: {slide.notes} -->\n")
        
        return "\n\n".join(content)
    
    def _format_html(self, slides: List[SlideContent]) -> str:
        """Format slides thành HTML"""
        html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Slide Presentation</title>
    <style>
        .slide { 
            page-break-after: always; 
            padding: 20px; 
            border-bottom: 2px solid #ccc; 
            margin-bottom: 20px;
        }
        .slide h1, .slide h2 { color: #2c3e50; }
        .slide h3 { color: #34495e; }
        .notes { font-style: italic; color: #7f8c8d; margin-top: 10px; }
    </style>
</head>
<body>
"""
        
        for slide in slides:
            html_content += f'<div class="slide">\n'
            # Convert markdown to basic HTML
            slide_html = slide.content.replace('# ', '<h1>').replace('## ', '<h2>').replace('### ', '<h3>')
            slide_html = slide_html.replace('\n\n', '</p><p>').replace('---', '')
            html_content += f'<p>{slide_html}</p>\n'
            
            if slide.notes:
                html_content += f'<div class="notes">Ghi chú: {slide.notes}</div>\n'
            
            html_content += '</div>\n\n'
        
        html_content += "</body></html>"
        return html_content
    
    def _format_powerpoint(self, slides: List[SlideContent]) -> str:
        """Format slides cho PowerPoint (trả về hướng dẫn)"""
        content = ["# Hướng dẫn tạo PowerPoint\n"]
        
        for i, slide in enumerate(slides, 1):
            content.append(f"## Slide {i}: {slide.title}")
            content.append(f"**Nội dung:**")
            content.append(slide.content.replace('---', '').strip())
            
            if slide.notes:
                content.append(f"**Ghi chú:** {slide.notes}")
            
            if slide.sources:
                content.append(f"**Nguồn:** {', '.join(slide.sources)}")
            
            content.append("\n" + "="*50 + "\n")
        
        return "\n".join(content)
    
    def _format_text(self, slides: List[SlideContent]) -> str:
        """Format slides thành text thuần"""
        content = []
        
        for slide in slides:
            content.append(f"SLIDE {slide.slide_number}: {slide.title.upper()}")
            content.append("="*50)
            
            # Remove markdown formatting
            text_content = slide.content.replace('#', '').replace('*', '').replace('---', '')
            text_content = text_content.replace('##', '').replace('###', '')
            content.append(text_content.strip())
            
            if slide.notes:
                content.append(f"\nGhi chú: {slide.notes}")
            
            content.append("\n" + "-"*50 + "\n")
        
        return "\n".join(content)