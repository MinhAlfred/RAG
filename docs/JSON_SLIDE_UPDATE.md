# JSON Slide Generation - Update Summary

## 🎯 Mục đích
Thêm JSON structure format cho slide generation API, giúp dễ dàng integrate với Spring Boot và tạo PPTX từ template.

## ✨ Các thay đổi chính

### 1. **Pydantic Models mới** (`src/sgk_rag/models/dto.py`)

#### Enums
- ✅ `SlideFormat.JSON` - Thêm JSON vào các format hỗ trợ
- ✅ `SlideType` - Định nghĩa 7 loại slide:
  - `TITLE` - Slide tiêu đề
  - `CONTENT` - Nội dung chính
  - `CODE` - Code examples
  - `IMAGE` - Hình ảnh
  - `TABLE` - Bảng biểu
  - `EXERCISE` - Bài tập
  - `SUMMARY` - Tóm tắt

#### Models
- ✅ `JsonSlideContent` - Structured slide với flexible content
  - Hỗ trợ nhiều field: `content`, `code`, `image_placeholder`, `caption`, `key_points`
  - Content có thể là: string, list, hoặc dict
  
- ✅ `JsonSlideMetadata` - Metadata đầy đủ
  - `total_slides`, `estimated_duration`, `sources`
  - `generated_at` (ISO timestamp), `grade_level`

- ✅ `JsonSlideResponse` - Type-safe response
  - Tích hợp `slides[]`, `metadata`, `status`, `processing_time`

### 2. **Slide Generator** (`src/sgk_rag/api/slide_generator.py`)

#### Methods mới
- ✅ `generate_slides_json()` - Tạo slides với JSON structure
- ✅ `_create_json_title_slide()` - Title slide JSON format
- ✅ `_create_json_content_slide()` - Content slide với flexible content
- ✅ `_create_json_exercise_slide()` - Exercise slide
- ✅ `_parse_content_to_bullets()` - Parse text thành list bullets
- ✅ `_generate_code_example()` - Tạo code examples tự động

#### Tính năng
- 🔥 **Auto-detect code slides**: Tự động tạo code slide nếu topic liên quan đến lập trình
- 🔥 **Smart content parsing**: Parse RAG response thành bullet points
- 🔥 **Source tracking**: Thu thập sources từ RAG và thêm vào metadata
- 🔥 **Error handling**: Fallback content nếu RAG fail

### 3. **API Endpoints** (`src/sgk_rag/api/main.py`)

#### Endpoint mới
```python
POST /slides/generate/json
```
- ✅ Trả về `JsonSlideResponse` thay vì `SlideResponse`
- ✅ Structured JSON dành riêng cho Spring Boot
- ✅ Type-safe với Pydantic validation

#### Endpoint cũ (giữ nguyên)
```python
POST /slides/generate
```
- ✅ Vẫn hỗ trợ markdown, html, powerpoint, text
- ✅ Redirect đến `/slides/generate/json` nếu request format=json

#### Updated
```python
GET /slides/formats
```
- ✅ Thêm JSON format vào danh sách

### 4. **Documentation**

#### `docs/SPRING_BOOT_INTEGRATION.md`
- ✅ Hướng dẫn đầy đủ integrate với Spring Boot
- ✅ Complete Java DTOs mapping
- ✅ Service layer implementation
- ✅ Apache POI PPTX generation code
- ✅ REST Controller examples
- ✅ cURL và Postman test examples

#### `scripts/test_json_slides.py`
- ✅ Test script cho JSON API
- ✅ Example Spring Boot code
- ✅ Tự động save JSON output

## 📊 JSON Response Example

```json
{
  "title": "Kiểu dữ liệu trong Python",
  "topic": "Python Data Types",
  "grade": 10,
  "slides": [
    {
      "slide_number": 1,
      "type": "title_slide",
      "title": "Kiểu dữ liệu trong Python",
      "subtitle": "Lớp 10 - Tin học",
      "key_points": [
        "Hiểu được khái niệm cơ bản",
        "Nắm được các thành phần",
        "Áp dụng vào thực tế"
      ]
    },
    {
      "slide_number": 2,
      "type": "content_slide",
      "title": "Các kiểu dữ liệu cơ bản",
      "content": [
        "int (số nguyên)",
        "float (số thực)",
        "str (xâu ký tự)",
        "bool (logic)"
      ],
      "notes": "Giải thích chi tiết cho giáo viên"
    },
    {
      "slide_number": 3,
      "type": "code_slide",
      "title": "Ví dụ minh họa",
      "code": "x = 10  # int\ny = 3.14  # float",
      "language": "python",
      "explanation": "Khai báo biến"
    }
  ],
  "metadata": {
    "total_slides": 3,
    "estimated_duration": "9 phút",
    "sources": ["SGK Tin học 10"],
    "generated_at": "2025-10-28T15:48:00Z",
    "grade_level": "Lớp 10"
  },
  "status": "success",
  "processing_time": 2.5
}
```

## 🚀 Cách sử dụng

### Python API
```bash
# Start API server
python scripts/run_api.py

# Test JSON endpoint
python scripts/test_json_slides.py
```

### cURL
```bash
curl -X POST http://localhost:8000/slides/generate/json \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Kiểu dữ liệu trong Python",
    "grade": 10,
    "slide_count": 5,
    "include_examples": true,
    "include_exercises": true
  }'
```

### Spring Boot
```java
// Call Python RAG API
JsonSlideResponse response = ragService.generateSlides(request);

// Map to PPTX
for (JsonSlideContent slide : response.getSlides()) {
    switch (slide.getType()) {
        case TITLE_SLIDE:
            pptxService.addTitleSlide(ppt, slide);
            break;
        case CONTENT_SLIDE:
            pptxService.addContentSlide(ppt, slide);
            break;
        case CODE_SLIDE:
            pptxService.addCodeSlide(ppt, slide);
            break;
    }
}
```

## 🎯 Flow hoàn chỉnh

```
Frontend (React) 
    ↓
Spring Boot Controller
    ↓
Call Python RAG API (/slides/generate/json)
    ↓
Python FastAPI
    ↓
RAG Pipeline (LangChain + Ollama)
    ↓
Return JSON Structure
    ↓
Spring Boot PPTX Service
    ↓
Map JSON → PPTX Template
    ↓
Return PPTX file to Frontend
```

## ✅ Lợi ích

1. **Type-safe**: Pydantic (Python) + Strong typing (Java)
2. **Flexible**: Content có thể là string, list, hoặc dict
3. **Easy mapping**: Trực tiếp từ JSON → PPTX slides
4. **Extensible**: Dễ thêm slide types mới
5. **Metadata rich**: Sources, duration, timestamp
6. **Backward compatible**: Giữ nguyên API cũ

## 🔧 Testing

```bash
# Test API
cd "f:\Ky 8\Capstone\RAG"
python scripts/test_json_slides.py

# Check output
cat output/json_slides_example.json
```

## 📚 Files thay đổi

- ✅ `src/sgk_rag/models/dto.py` - Added JSON models
- ✅ `src/sgk_rag/api/slide_generator.py` - Added JSON methods
- ✅ `src/sgk_rag/api/main.py` - Added `/slides/generate/json` endpoint
- ✅ `scripts/test_json_slides.py` - Test script
- ✅ `docs/SPRING_BOOT_INTEGRATION.md` - Integration guide

## 🎓 Next Steps

1. ✅ Test JSON API endpoint
2. ⏳ Implement Spring Boot service
3. ⏳ Create PPTX templates
4. ⏳ Build frontend UI
5. ⏳ Deploy to production

---
**Status**: ✅ Ready for testing  
**Created**: 2025-10-28  
**Version**: 1.0.0
