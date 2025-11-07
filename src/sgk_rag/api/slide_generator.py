"""Slide Generator - Tạo nội dung slide từ SGK Informatics"""

import json
import time
from typing import List, Dict, Optional, Any, Union
from pathlib import Path
from datetime import datetime

from ..core.rag_pipeline import RAGPipeline
from ..models.dto import (
    SlideContent, SlideRequest, SlideFormat, SlideType,
    JsonSlideContent, JsonSlideResponse, JsonSlideMetadata,
    PowerPointLayout, PlaceholderType, PlaceholderContent, BulletPoint,
    TextAlignment, Position, CodeBlock, ImagePlaceholder
)


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
        elif format_type == SlideFormat.JSON:
            # JSON format không dùng method này, sử dụng generate_slides_json()
            return json.dumps({"error": "Use generate_slides_json() for JSON format"}, ensure_ascii=False, indent=2)
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
    
    # ========== JSON STRUCTURE METHODS FOR SPRING BOOT ==========
    
    def generate_slides_json(self, request: SlideRequest) -> JsonSlideResponse:
        """
        Tạo slides với JSON structure cho Spring Boot
        
        Args:
            request: SlideRequest chứa thông tin yêu cầu
            
        Returns:
            JsonSlideResponse: Structured JSON response
        """
        start_time = time.time()
        
        try:
            json_slides = []
            all_sources = []
            
            # Slide 1: Title slide
            title_slide = self._create_json_title_slide(request.topic, request.grade)
            json_slides.append(title_slide)
            
            # Tạo outline cho các slide content
            outline = self._generate_outline(request.topic, request.slide_count - 1, request.grade)
            
            # Tạo content slides
            for i, section in enumerate(outline, 2):
                slide_data = self._create_json_content_slide(
                    slide_number=i,
                    section=section,
                    topic=request.topic,
                    grade=request.grade,
                    include_examples=request.include_examples
                )
                json_slides.append(slide_data['slide'])
                all_sources.extend(slide_data.get('sources', []))
            
            # Thêm slide bài tập nếu được yêu cầu
            if request.include_exercises and len(json_slides) < request.slide_count:
                exercise_slide = self._create_json_exercise_slide(
                    slide_number=len(json_slides) + 1,
                    topic=request.topic,
                    grade=request.grade
                )
                json_slides.append(exercise_slide)
            
            # Limit slides to requested count
            json_slides = json_slides[:request.slide_count]
            
            # Tạo metadata
            processing_time = time.time() - start_time
            metadata = JsonSlideMetadata(
                total_slides=len(json_slides),
                estimated_duration=f"{len(json_slides) * 3} phút",
                sources=list(set(all_sources))[:5],  # Top 5 unique sources
                generated_at=datetime.now().isoformat(),
                grade_level=f"Lớp {request.grade}" if request.grade else "Trung học"
            )
            
            # Tạo response
            response = JsonSlideResponse(
                title=request.topic,
                topic=request.topic,
                grade=request.grade,
                slides=json_slides,
                metadata=metadata,
                status="success",
                processing_time=round(processing_time, 2)
            )
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"Lỗi khi tạo JSON slides: {e}")
            
            # Return error response
            return JsonSlideResponse(
                title=request.topic,
                topic=request.topic,
                grade=request.grade,
                slides=[],
                metadata=JsonSlideMetadata(
                    total_slides=0,
                    estimated_duration="0 phút",
                    sources=[],
                    generated_at=datetime.now().isoformat(),
                    grade_level=f"Lớp {request.grade}" if request.grade else "Trung học"
                ),
                status="error",
                processing_time=round(processing_time, 2),
                error=str(e)
            )
    
    def _create_json_title_slide(self, topic: str, grade: Optional[int]) -> JsonSlideContent:
        """Tạo title slide với JSON structure cho Apache POI"""
        grade_text = f"Lớp {grade}" if grade else "Tin học"

        # Create placeholder content for Apache POI
        placeholders = [
            PlaceholderContent(
                placeholder_type=PlaceholderType.TITLE,
                text_content=topic,
                alignment=TextAlignment.CENTER
            ),
            PlaceholderContent(
                placeholder_type=PlaceholderType.SUBTITLE,
                text_content=grade_text,
                alignment=TextAlignment.CENTER
            )
        ]

        return JsonSlideContent(
            slide_number=1,
            type=SlideType.TITLE,
            layout=PowerPointLayout.TITLE,
            placeholders=placeholders,
            title=topic,
            subtitle=grade_text,
            notes=f"Slide giới thiệu về chủ đề {topic}",
            key_points=[
                f"Hiểu được khái niệm cơ bản về {topic.lower()}",
                "Nắm được các thành phần và chức năng chính",
                "Áp dụng kiến thức vào thực tế"
            ]
        )
    
    def _create_json_content_slide(self, slide_number: int, section: str, topic: str,
                                  grade: Optional[int], include_examples: bool) -> Dict[str, Any]:
        """Tạo content slide với JSON structure"""
        
        # Tạo câu hỏi chi tiết cho section
        content_question = f"""
        Tạo slide về "{section}" trong chủ đề "{topic}" cho học sinh lớp {grade if grade else 'trung học'}.

        YÊU CẦU BẮT BUỘC:
        1. Tạo 4-6 bullet points NGẮN GỌN (tối đa 8-10 từ mỗi điểm)
        2. Mỗi điểm phải súc tích, dễ nhớ, dễ đọc
        3. Không giải thích dài dòng - chỉ nêu ý chính
        4. Sử dụng từ khóa, tránh câu văn dài

        FORMAT SLIDE HIỆU QUẢ:
        - Bullet points: 8-10 từ tối đa
        - Một ý chính mỗi bullet
        - Không dùng câu phức tạp
        - Dùng động từ mạnh

        VÍ DỤ TỐT:
        • int - Số nguyên không có phần thập phân
        • float - Số thực với phần thập phân
        • str - Xâu ký tự, văn bản

        VÍ DỤ XẤU (quá dài):
        • int là kiểu dữ liệu số nguyên dùng để lưu trữ các số không có phần thập phân và có thể dương hoặc âm

        CHỈ TRẢ VỀ BULLET POINTS, không giải thích thêm.
        """
        
        try:
            content_response = self.rag_pipeline.query(
                content_question,
                grade_filter=grade,
                return_sources=True
            )
            
            # Parse response
            if isinstance(content_response, dict):
                content_text = content_response.get('answer', str(content_response))
                response_sources = content_response.get('sources', [])
            else:
                content_text = str(content_response)
                response_sources = []
            
            # Parse content thành list of bullet points
            content_bullets = self._parse_content_to_bullets(content_text)
            
            # Chỉ tạo code example khi section yêu cầu ví dụ code
            code_data = None
            if include_examples:
                # Chỉ tạo code nếu section rõ ràng về code/ví dụ
                needs_code = any(keyword in section.lower() 
                               for keyword in ['ví dụ', 'example', 'minh họa code', 'viết code', 
                                              'cú pháp', 'syntax', 'cách viết'])
                # VÀ topic là về lập trình
                is_programming = any(keyword in topic.lower() 
                                   for keyword in ['python', 'lập trình', 'code', 'hàm', 'function',
                                                  'biến', 'variable', 'kiểu dữ liệu', 'data type'])
                
                if needs_code and is_programming:
                    code_data = self._generate_code_example(section, topic, grade)
            
            # Convert content bullets to BulletPoint objects with formatting
            formatted_bullets = []
            for i, bullet_text in enumerate(content_bullets):
                # First bullet is main point (level 0), rest are sub-points (level 1)
                level = 0 if i == 0 else 1
                formatted_bullets.append(BulletPoint(
                    text=bullet_text,
                    level=level,
                    bold=(i == 0),  # First bullet is bold
                    font_size=18 if level == 0 else 16
                ))

            # Create placeholder content for Apache POI
            placeholders = [
                PlaceholderContent(
                    placeholder_type=PlaceholderType.TITLE,
                    text_content=section,
                    alignment=TextAlignment.LEFT
                ),
                PlaceholderContent(
                    placeholder_type=PlaceholderType.BODY,
                    bullet_points=formatted_bullets,
                    alignment=TextAlignment.LEFT
                )
            ]

            # Determine if we should create a code slide
            should_create_code_slide = (
                code_data and
                include_examples and
                any(keyword in section.lower()
                    for keyword in ['ví dụ', 'example', 'minh họa', 'code', 'lập trình'])
            )

            if should_create_code_slide:
                # Code slide with structured code block
                code_block = CodeBlock(
                    code=code_data['code'],
                    language=code_data.get('language', 'python'),
                    font_family="Courier New",
                    font_size=10,
                    position=Position(x=1.0, y=2.5, width=8.5, height=4.0)
                )

                slide = JsonSlideContent(
                    slide_number=slide_number,
                    type=SlideType.CODE,
                    layout=PowerPointLayout.TITLE_AND_CONTENT,
                    placeholders=placeholders,
                    title=section,
                    content=content_bullets,
                    code_block=code_block,
                    notes=f"Slide code về {section} trong chủ đề {topic}",
                    key_points=content_bullets[:3],
                    # Deprecated fields for backward compatibility
                    code=code_data['code'],
                    language=code_data.get('language', 'python'),
                    explanation=code_data.get('explanation', f"Ví dụ về {section}")
                )
            else:
                # Content slide with structured bullet points
                slide = JsonSlideContent(
                    slide_number=slide_number,
                    type=SlideType.CONTENT,
                    layout=PowerPointLayout.TITLE_AND_CONTENT,
                    placeholders=placeholders,
                    title=section,
                    content=content_bullets,
                    notes=f"Slide về {section} trong chủ đề {topic}",
                    key_points=content_bullets[:3] if len(content_bullets) > 3 else content_bullets
                )
            
            # Collect sources
            sources = []
            for source in response_sources:
                if isinstance(source, dict):
                    metadata = source.get('metadata', {})
                    lesson_title = metadata.get('lesson_title', 'Chưa xác định')
                    grade_info = metadata.get('grade', 'N/A')
                    sources.append(f"SGK Tin học Lớp {grade_info} - {lesson_title}")
            
            return {
                'slide': slide,
                'sources': sources
            }
            
        except Exception as e:
            print(f"Lỗi khi tạo JSON content slide: {e}")
            
            # Fallback slide
            fallback_slide = JsonSlideContent(
                slide_number=slide_number,
                type=SlideType.CONTENT,
                title=section,
                content=[f"Nội dung về {section} trong {topic}"],
                notes=f"Slide về {section}",
                key_points=[section]
            )
            
            return {
                'slide': fallback_slide,
                'sources': []
            }
    
    def _create_json_exercise_slide(self, slide_number: int, topic: str, grade: Optional[int]) -> JsonSlideContent:
        """Tạo exercise slide với JSON structure cho Apache POI"""

        exercise_question = f"""
        Tạo 3-5 câu hỏi bài tập về "{topic}" phù hợp với học sinh lớp {grade if grade else 'trung học'}.

        Yêu cầu:
        - Câu hỏi từ dễ đến khó
        - Bao gồm cả lý thuyết và thực hành
        - Phù hợp với nội dung sách giáo khoa

        Chỉ liệt kê các câu hỏi, mỗi câu trên một dòng.
        """

        try:
            exercise_response = self.rag_pipeline.query(
                exercise_question,
                grade_filter=grade,
                return_sources=False
            )

            if isinstance(exercise_response, dict):
                exercise_text = exercise_response.get('answer', str(exercise_response))
            else:
                exercise_text = str(exercise_response)

            # Parse exercises thành list
            exercises = self._parse_content_to_bullets(exercise_text)

            # Convert to formatted bullet points
            exercise_bullets = [
                BulletPoint(text=ex, level=0, font_size=16)
                for ex in exercises
            ]

            # Create placeholders for Apache POI
            placeholders = [
                PlaceholderContent(
                    placeholder_type=PlaceholderType.TITLE,
                    text_content="Bài tập thực hành",
                    alignment=TextAlignment.LEFT
                ),
                PlaceholderContent(
                    placeholder_type=PlaceholderType.BODY,
                    bullet_points=exercise_bullets,
                    alignment=TextAlignment.LEFT
                )
            ]

            return JsonSlideContent(
                slide_number=slide_number,
                type=SlideType.EXERCISE,
                layout=PowerPointLayout.TITLE_AND_CONTENT,
                placeholders=placeholders,
                title="Bài tập thực hành",
                content=exercises,
                notes="Thảo luận nhóm 5 phút, sau đó trình bày kết quả",
                key_points=[
                    "Thảo luận nhóm",
                    "Trình bày kết quả",
                    "Giáo viên nhận xét"
                ]
            )

        except Exception as e:
            print(f"Lỗi khi tạo JSON exercise slide: {e}")

            # Fallback exercises
            fallback_exercises = [
                f"Nêu khái niệm cơ bản về {topic}?",
                f"Liệt kê các thành phần chính của {topic}?",
                f"Cho ví dụ ứng dụng của {topic} trong thực tế?"
            ]

            fallback_bullets = [
                BulletPoint(text=ex, level=0, font_size=16)
                for ex in fallback_exercises
            ]

            placeholders = [
                PlaceholderContent(
                    placeholder_type=PlaceholderType.TITLE,
                    text_content="Bài tập thực hành",
                    alignment=TextAlignment.LEFT
                ),
                PlaceholderContent(
                    placeholder_type=PlaceholderType.BODY,
                    bullet_points=fallback_bullets,
                    alignment=TextAlignment.LEFT
                )
            ]

            return JsonSlideContent(
                slide_number=slide_number,
                type=SlideType.EXERCISE,
                layout=PowerPointLayout.TITLE_AND_CONTENT,
                placeholders=placeholders,
                title="Bài tập thực hành",
                content=fallback_exercises,
                notes="Thảo luận nhóm và trình bày",
                key_points=["Thảo luận", "Trình bày", "Nhận xét"]
            )
    
    def _make_bullet_concise(self, text: str, max_chars: int = 80) -> str:
        """Make bullet point concise for better presentation"""
        # Remove extra whitespace
        text = ' '.join(text.split())

        # If already short, return as is
        if len(text) <= max_chars:
            return text

        # Try to truncate at word boundary
        if len(text) > max_chars:
            truncated = text[:max_chars].rsplit(' ', 1)[0]
            # Only add ellipsis if we cut off significant content
            if len(text) - len(truncated) > 10:
                return truncated + '...'
            return truncated

        return text

    def _parse_content_to_bullets(self, text: str) -> List[str]:
        """Parse text thành list of concise bullet points (good for presentations)"""
        bullets = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()

            # Skip empty lines and markdown headers
            if not line or line.startswith('##') or line.startswith('#'):
                continue

            # Remove bullet markers and numbering
            clean_line = line.lstrip('0123456789.-*•:)→ ').strip()

            # Skip very short lines (likely not real content)
            if len(clean_line) < 5:
                continue

            # Skip lines that look like instructions or meta-content
            if any(keyword in clean_line.lower() for keyword in ['ví dụ tốt', 'ví dụ xấu', 'yêu cầu', 'format']):
                continue

            # Make bullet concise (max 80 chars)
            concise_bullet = self._make_bullet_concise(clean_line, max_chars=80)

            # Add to bullets list
            if concise_bullet and len(concise_bullet) >= 5:
                bullets.append(concise_bullet)

        # If no bullets found, try to split by sentences
        if not bullets:
            sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 10]
            for sentence in sentences[:6]:
                concise = self._make_bullet_concise(sentence, max_chars=80)
                if concise:
                    bullets.append(concise)

        # Fallback: use first 80 chars of text
        if not bullets and text.strip():
            bullets.append(self._make_bullet_concise(text, max_chars=80))

        # Limit to 5-6 bullets per slide (presentation best practice)
        return bullets[:6]
    
    def _generate_code_example(self, section: str, topic: str, grade: Optional[int]) -> Optional[Dict[str, str]]:
        """Tạo code example nếu phù hợp"""
        
        code_question = f"""
        Cho một ví dụ code Python ngắn gọn (3-5 dòng) về {section} trong {topic}.
        Chỉ trả về code, không giải thích.
        """
        
        try:
            code_response = self.rag_pipeline.query(
                code_question,
                grade_filter=grade,
                return_sources=False
            )
            
            if isinstance(code_response, dict):
                code_text = code_response.get('answer', '')
            else:
                code_text = str(code_response)
            
            # Extract code block nếu có
            code_text = code_text.strip()
            if '```' in code_text:
                # Extract code từ markdown code block
                parts = code_text.split('```')
                if len(parts) >= 2:
                    code_text = parts[1]
                    # Remove language identifier
                    if '\n' in code_text:
                        code_text = '\n'.join(code_text.split('\n')[1:])
            
            # Validate có phải code không
            if len(code_text) > 10 and len(code_text) < 500:
                return {
                    'code': code_text.strip(),
                    'language': 'python',
                    'explanation': f"Ví dụ về {section}"
                }
            
            return None
            
        except Exception as e:
            print(f"Không thể tạo code example: {e}")
            return None