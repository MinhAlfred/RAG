# Spring Boot Integration Guide - JSON Slide API

## 📖 Tổng quan

API `/slides/generate/json` trả về **structured JSON** được thiết kế để dễ dàng integrate với Spring Boot và xử lý bằng Apache POI PPTX.

## 🎯 Flow hoàn chỉnh

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐      ┌──────────┐
│   Frontend  │─────>│ Spring Boot  │─────>│ Python RAG  │─────>│ LangChain│
│   (React)   │      │  Controller  │      │  FastAPI    │      │ + Ollama │
└─────────────┘      └──────────────┘      └─────────────┘      └──────────┘
                            │                      │
                            │  JSON Response       │
                            │<─────────────────────┘
                            ▼
                     ┌──────────────┐
                     │ PPTX Template│
                     │   Service    │
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Final PPTX  │
                     │    File      │
                     └──────────────┘
```

## 📊 JSON Response Structure

### Response Model
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
      "notes": "Slide giới thiệu",
      "key_points": ["Mục tiêu 1", "Mục tiêu 2"]
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
      "notes": "Giải thích chi tiết cho giáo viên",
      "key_points": ["int", "float", "str", "bool"]
    },
    {
      "slide_number": 3,
      "type": "code_slide",
      "title": "Ví dụ minh họa",
      "code": "x = 10  # int\ny = 3.14  # float",
      "language": "python",
      "explanation": "Khai báo biến với các kiểu khác nhau"
    }
  ],
  "metadata": {
    "total_slides": 3,
    "estimated_duration": "15 phút",
    "sources": ["SGK Tin học 10"],
    "generated_at": "2025-10-28T15:48:00Z",
    "grade_level": "Lớp 10"
  },
  "status": "success",
  "processing_time": 2.5
}
```

## 🔧 Slide Types

| Type | Description | Content Format |
|------|-------------|----------------|
| `title_slide` | Slide tiêu đề | `subtitle`, `key_points` |
| `content_slide` | Nội dung chính | `content` (string hoặc list) |
| `code_slide` | Code examples | `code`, `language`, `explanation` |
| `image_slide` | Hình ảnh minh họa | `image_placeholder`, `caption` |
| `exercise_slide` | Bài tập | `content` (list câu hỏi) |
| `summary_slide` | Tóm tắt | `content`, `key_points` |

## ☕ Spring Boot Implementation

### 1. Dependencies (pom.xml)
```xml
<dependencies>
    <!-- Spring Boot Web -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    
    <!-- Apache POI for PPTX -->
    <dependency>
        <groupId>org.apache.poi</groupId>
        <artifactId>poi-ooxml</artifactId>
        <version>5.2.3</version>
    </dependency>
    
    <!-- Lombok for DTOs -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <scope>provided</scope>
    </dependency>
    
    <!-- Jackson for JSON -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
    </dependency>
</dependencies>
```

### 2. DTOs (Data Transfer Objects)

#### JsonSlideResponse.java
```java
package com.example.presentation.dto;

import lombok.Data;
import java.util.List;

@Data
public class JsonSlideResponse {
    private String title;
    private String topic;
    private Integer grade;
    private List<JsonSlideContent> slides;
    private JsonSlideMetadata metadata;
    private String status;
    private Double processingTime;
    private String error;
}
```

#### JsonSlideContent.java
```java
package com.example.presentation.dto;

import lombok.Data;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

@Data
public class JsonSlideContent {
    @JsonProperty("slide_number")
    private Integer slideNumber;
    
    private SlideType type;
    private String title;
    private Object content;  // Flexible: String, List<String>, or Map
    
    private String subtitle;
    private String code;
    private String language;
    
    @JsonProperty("image_placeholder")
    private String imagePlaceholder;
    
    private String caption;
    private String explanation;
    private String notes;
    
    @JsonProperty("key_points")
    private List<String> keyPoints;
}
```

#### SlideType.java
```java
package com.example.presentation.dto;

import com.fasterxml.jackson.annotation.JsonValue;

public enum SlideType {
    TITLE_SLIDE("title_slide"),
    CONTENT_SLIDE("content_slide"),
    CODE_SLIDE("code_slide"),
    IMAGE_SLIDE("image_slide"),
    EXERCISE_SLIDE("exercise_slide"),
    SUMMARY_SLIDE("summary_slide");
    
    private final String value;
    
    SlideType(String value) {
        this.value = value;
    }
    
    @JsonValue
    public String getValue() {
        return value;
    }
}
```

#### JsonSlideMetadata.java
```java
package com.example.presentation.dto;

import lombok.Data;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

@Data
public class JsonSlideMetadata {
    @JsonProperty("total_slides")
    private Integer totalSlides;
    
    @JsonProperty("estimated_duration")
    private String estimatedDuration;
    
    private List<String> sources;
    
    @JsonProperty("generated_at")
    private String generatedAt;
    
    @JsonProperty("grade_level")
    private String gradeLevel;
}
```

### 3. Service Layer

#### RagApiService.java
```java
package com.example.presentation.service;

import com.example.presentation.dto.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class RagApiService {
    
    @Value("${python.rag.api.url:http://localhost:8000}")
    private String ragApiUrl;
    
    private final RestTemplate restTemplate;
    
    public RagApiService() {
        this.restTemplate = new RestTemplate();
    }
    
    public JsonSlideResponse generateSlides(SlideRequest request) {
        String url = ragApiUrl + "/slides/generate/json";
        
        log.info("Calling Python RAG API: {}", url);
        log.info("Request: {}", request);
        
        try {
            JsonSlideResponse response = restTemplate.postForObject(
                url,
                request,
                JsonSlideResponse.class
            );
            
            log.info("Received {} slides from RAG API", 
                response != null ? response.getSlides().size() : 0);
            
            return response;
            
        } catch (Exception e) {
            log.error("Error calling RAG API: {}", e.getMessage());
            throw new RuntimeException("Failed to generate slides from RAG", e);
        }
    }
}
```

#### PptxGenerationService.java
```java
package com.example.presentation.service;

import com.example.presentation.dto.*;
import org.apache.poi.xslf.usermodel.*;
import org.springframework.stereotype.Service;
import lombok.extern.slf4j.Slf4j;

import java.awt.*;
import java.awt.geom.Rectangle2D;
import java.io.*;
import java.util.List;

@Slf4j
@Service
public class PptxGenerationService {
    
    private static final int SLIDE_WIDTH = 720;
    private static final int SLIDE_HEIGHT = 540;
    
    public byte[] generatePptxFromJson(JsonSlideResponse ragResponse) throws IOException {
        // Create new presentation
        XMLSlideShow ppt = new XMLSlideShow();
        ppt.setPageSize(new Dimension(SLIDE_WIDTH, SLIDE_HEIGHT));
        
        // Process each slide
        for (JsonSlideContent slideData : ragResponse.getSlides()) {
            switch (slideData.getType()) {
                case TITLE_SLIDE:
                    addTitleSlide(ppt, slideData);
                    break;
                    
                case CONTENT_SLIDE:
                    addContentSlide(ppt, slideData);
                    break;
                    
                case CODE_SLIDE:
                    addCodeSlide(ppt, slideData);
                    break;
                    
                case EXERCISE_SLIDE:
                    addExerciseSlide(ppt, slideData);
                    break;
                    
                default:
                    addGenericSlide(ppt, slideData);
            }
        }
        
        // Convert to bytes
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ppt.write(out);
        ppt.close();
        
        return out.toByteArray();
    }
    
    private void addTitleSlide(XMLSlideShow ppt, JsonSlideContent slide) {
        XSLFSlide pptSlide = ppt.createSlide();
        
        // Title
        XSLFTextShape title = pptSlide.createTextBox();
        title.setAnchor(new Rectangle2D.Double(50, 150, 620, 100));
        XSLFTextParagraph para = title.addNewTextParagraph();
        para.setTextAlign(TextParagraph.TextAlign.CENTER);
        XSLFTextRun run = para.addNewTextRun();
        run.setText(slide.getTitle());
        run.setFontSize(44.0);
        run.setBold(true);
        
        // Subtitle
        if (slide.getSubtitle() != null) {
            XSLFTextShape subtitle = pptSlide.createTextBox();
            subtitle.setAnchor(new Rectangle2D.Double(50, 280, 620, 60));
            XSLFTextParagraph subPara = subtitle.addNewTextParagraph();
            subPara.setTextAlign(TextParagraph.TextAlign.CENTER);
            XSLFTextRun subRun = subPara.addNewTextRun();
            subRun.setText(slide.getSubtitle());
            subRun.setFontSize(24.0);
        }
    }
    
    private void addContentSlide(XMLSlideShow ppt, JsonSlideContent slide) {
        XSLFSlide pptSlide = ppt.createSlide();
        
        // Title
        addSlideTitle(pptSlide, slide.getTitle());
        
        // Content
        XSLFTextShape content = pptSlide.createTextBox();
        content.setAnchor(new Rectangle2D.Double(50, 120, 620, 380));
        
        Object contentData = slide.getContent();
        
        if (contentData instanceof List) {
            // Bullet points
            List<?> items = (List<?>) contentData;
            for (Object item : items) {
                XSLFTextParagraph para = content.addNewTextParagraph();
                para.setIndentLevel(0);
                para.setBullet(true);
                XSLFTextRun run = para.addNewTextRun();
                run.setText(item.toString());
                run.setFontSize(18.0);
            }
        } else {
            // Plain text
            XSLFTextParagraph para = content.addNewTextParagraph();
            XSLFTextRun run = para.addNewTextRun();
            run.setText(contentData.toString());
            run.setFontSize(18.0);
        }
    }
    
    private void addCodeSlide(XMLSlideShow ppt, JsonSlideContent slide) {
        XSLFSlide pptSlide = ppt.createSlide();
        
        // Title
        addSlideTitle(pptSlide, slide.getTitle());
        
        // Code block
        XSLFTextShape codeBox = pptSlide.createTextBox();
        codeBox.setAnchor(new Rectangle2D.Double(50, 120, 620, 300));
        
        XSLFTextParagraph para = codeBox.addNewTextParagraph();
        XSLFTextRun run = para.addNewTextRun();
        run.setText(slide.getCode());
        run.setFontFamily("Courier New");
        run.setFontSize(14.0);
        
        // Explanation
        if (slide.getExplanation() != null) {
            XSLFTextShape explanation = pptSlide.createTextBox();
            explanation.setAnchor(new Rectangle2D.Double(50, 440, 620, 60));
            XSLFTextParagraph expPara = explanation.addNewTextParagraph();
            XSLFTextRun expRun = expPara.addNewTextRun();
            expRun.setText(slide.getExplanation());
            expRun.setFontSize(14.0);
            expRun.setItalic(true);
        }
    }
    
    private void addExerciseSlide(XMLSlideShow ppt, JsonSlideContent slide) {
        // Similar to content slide but with different styling
        addContentSlide(ppt, slide);
    }
    
    private void addGenericSlide(XMLSlideShow ppt, JsonSlideContent slide) {
        addContentSlide(ppt, slide);
    }
    
    private void addSlideTitle(XSLFSlide slide, String titleText) {
        XSLFTextShape title = slide.createTextBox();
        title.setAnchor(new Rectangle2D.Double(50, 40, 620, 60));
        XSLFTextParagraph para = title.addNewTextParagraph();
        XSLFTextRun run = para.addNewTextRun();
        run.setText(titleText);
        run.setFontSize(32.0);
        run.setBold(true);
    }
}
```

### 4. Controller

#### PresentationController.java
```java
package com.example.presentation.controller;

import com.example.presentation.dto.*;
import com.example.presentation.service.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RestController
@RequestMapping("/api/presentations")
@CrossOrigin(origins = "*")
public class PresentationController {
    
    @Autowired
    private RagApiService ragApiService;
    
    @Autowired
    private PptxGenerationService pptxService;
    
    @PostMapping("/generate")
    public ResponseEntity<byte[]> generatePresentation(@RequestBody SlideRequest request) {
        try {
            log.info("Generating presentation for topic: {}", request.getTopic());
            
            // Step 1: Call Python RAG API
            JsonSlideResponse ragResponse = ragApiService.generateSlides(request);
            
            if (!"success".equals(ragResponse.getStatus())) {
                throw new RuntimeException("RAG API failed: " + ragResponse.getError());
            }
            
            log.info("Generated {} slides from RAG", ragResponse.getSlides().size());
            
            // Step 2: Generate PPTX from JSON
            byte[] pptxBytes = pptxService.generatePptxFromJson(ragResponse);
            
            log.info("PPTX generated successfully, size: {} bytes", pptxBytes.length);
            
            // Step 3: Return PPTX file
            String filename = ragResponse.getTitle()
                .replaceAll("[^a-zA-Z0-9\\s]", "")
                .replaceAll("\\s+", "_") + ".pptx";
            
            return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, 
                    "attachment; filename=\"" + filename + "\"")
                .contentType(MediaType.parseMediaType(
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation"))
                .body(pptxBytes);
            
        } catch (Exception e) {
            log.error("Error generating presentation: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
    
    @GetMapping("/preview")
    public ResponseEntity<JsonSlideResponse> previewSlides(
            @RequestParam String topic,
            @RequestParam(required = false) Integer grade,
            @RequestParam(defaultValue = "5") int slideCount) {
        
        try {
            SlideRequest request = new SlideRequest();
            request.setTopic(topic);
            request.setGrade(grade);
            request.setSlideCount(slideCount);
            request.setIncludeExamples(true);
            
            JsonSlideResponse response = ragApiService.generateSlides(request);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("Error previewing slides: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
```

### 5. Configuration

#### application.yml
```yaml
server:
  port: 8080

python:
  rag:
    api:
      url: http://localhost:8000

spring:
  servlet:
    multipart:
      max-file-size: 50MB
      max-request-size: 50MB

logging:
  level:
    com.example.presentation: DEBUG
```

## 🔄 API Usage Examples

### Test với cURL
```bash
# Generate presentation
curl -X POST http://localhost:8080/api/presentations/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Kiểu dữ liệu trong Python",
    "grade": 10,
    "slide_count": 5,
    "include_examples": true,
    "include_exercises": true
  }' \
  --output presentation.pptx

# Preview slides (JSON only)
curl "http://localhost:8080/api/presentations/preview?topic=Python&grade=10&slideCount=3"
```

### Test với Postman
1. POST `http://localhost:8080/api/presentations/generate`
2. Body (JSON):
```json
{
  "topic": "Kiểu dữ liệu trong Python",
  "grade": 10,
  "slide_count": 5,
  "include_examples": true,
  "include_exercises": true
}
```
3. Send → Download PPTX file

## 📝 Lợi ích của JSON Structure

### ✅ Advantages
1. **Type-safe**: Pydantic validation ở Python, Strong typing ở Java
2. **Flexible content**: Hỗ trợ nhiều format (string, list, code)
3. **Easy mapping**: Trực tiếp map JSON → PPTX slides
4. **Extensible**: Dễ thêm slide types mới
5. **Metadata rich**: Tracking sources, duration, timestamp
6. **Error handling**: Status, error messages built-in

### 🎯 Use Cases
- Tạo slide tự động từ SGK
- LMS (Learning Management System)
- E-learning platforms
- Teacher tools
- Student study aids

## 📚 Resources
- [Apache POI Documentation](https://poi.apache.org/components/slideshow/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Models](https://docs.pydantic.dev/)

---
**Created by**: RAG System Team  
**Last Updated**: 2025-10-28
