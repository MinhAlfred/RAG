"""Test JSON Slide Generation - Demo cho Spring Boot integration"""

import requests
import json
from typing import Dict, Any


def test_json_slide_generation():
    """Test tạo slides với JSON structure"""
    
    # API endpoint
    url = "http://localhost:8000/slides/generate/json"
    
    # Request data
    request_data = {
        "topic": "Kiểu dữ liệu trong Python",
        "grade": 10,
        "slide_count": 5,
        "include_examples": True,
        "include_exercises": True
    }
    
    print("=" * 70)
    print("🧪 Testing JSON Slide Generation")
    print("=" * 70)
    print(f"\n📝 Request:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    try:
        print(f"\n🚀 Sending request to {url}...")
        response = requests.post(url, json=request_data, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ Response received successfully!")
            print("=" * 70)
            
            # Print metadata
            print(f"\n📊 Metadata:")
            print(f"   Title: {data.get('title')}")
            print(f"   Grade: {data.get('grade')}")
            print(f"   Total Slides: {data['metadata']['total_slides']}")
            print(f"   Duration: {data['metadata']['estimated_duration']}")
            print(f"   Generated: {data['metadata']['generated_at']}")
            print(f"   Processing Time: {data['processing_time']}s")
            
            # Print sources
            if data['metadata'].get('sources'):
                print(f"\n📚 Sources:")
                for source in data['metadata']['sources']:
                    print(f"   - {source}")
            
            # Print each slide
            print(f"\n📑 Slides:")
            for slide in data['slides']:
                print(f"\n{'='*70}")
                print(f"Slide {slide['slide_number']}: {slide['title']}")
                print(f"Type: {slide['type']}")
                
                if slide.get('subtitle'):
                    print(f"Subtitle: {slide['subtitle']}")
                
                if slide.get('content'):
                    print(f"\nContent:")
                    content = slide['content']
                    if isinstance(content, list):
                        for item in content:
                            print(f"  • {item}")
                    else:
                        print(f"  {content}")
                
                if slide.get('code'):
                    print(f"\nCode ({slide.get('language', 'python')}):")
                    print(f"```{slide.get('language', 'python')}")
                    print(slide['code'])
                    print("```")
                
                if slide.get('explanation'):
                    print(f"\nExplanation: {slide['explanation']}")
                
                if slide.get('key_points'):
                    print(f"\nKey Points:")
                    for point in slide['key_points']:
                        print(f"  ✓ {point}")
                
                if slide.get('notes'):
                    print(f"\n💡 Notes: {slide['notes']}")
            
            # Save to file
            output_file = "output/json_slides_example.json"
            import os
            os.makedirs("output", exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"\n\n💾 Full JSON saved to: {output_file}")
            print("\n" + "="*70)
            print("✅ Test completed successfully!")
            
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API server")
        print("   Make sure the API server is running: python scripts/run_api.py")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")


def print_spring_boot_example():
    """In ví dụ code Spring Boot để consume JSON"""
    
    print("\n" + "="*70)
    print("☕ Spring Boot Integration Example")
    print("="*70)
    
    java_code = """
// Pydantic models tương ứng với Java DTOs

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

@Data
public class JsonSlideContent {
    private Integer slideNumber;
    private SlideType type;
    private String title;
    private Object content;  // Can be String, List<String>, or Map
    private String subtitle;
    private String code;
    private String language;
    private String imageplaceholder;
    private String caption;
    private String explanation;
    private String notes;
    private List<String> keyPoints;
}

@Data
public class JsonSlideMetadata {
    private Integer totalSlides;
    private String estimatedDuration;
    private List<String> sources;
    private String generatedAt;
    private String gradeLevel;
}

enum SlideType {
    TITLE_SLIDE,
    CONTENT_SLIDE,
    CODE_SLIDE,
    IMAGE_SLIDE,
    TABLE_SLIDE,
    EXERCISE_SLIDE,
    SUMMARY_SLIDE
}

// Service to call Python RAG API
@Service
public class SlideGenerationService {
    
    @Autowired
    private RestTemplate restTemplate;
    
    @Value("${python.rag.api.url}")
    private String pythonApiUrl;
    
    public JsonSlideResponse generateSlides(SlideRequest request) {
        String url = pythonApiUrl + "/slides/generate/json";
        
        ResponseEntity<JsonSlideResponse> response = restTemplate.postForEntity(
            url,
            request,
            JsonSlideResponse.class
        );
        
        return response.getBody();
    }
}

// Controller to generate PPTX
@RestController
@RequestMapping("/api/presentations")
public class PresentationController {
    
    @Autowired
    private SlideGenerationService slideService;
    
    @Autowired
    private PptxTemplateService pptxService;
    
    @PostMapping("/generate")
    public ResponseEntity<byte[]> generatePresentation(@RequestBody SlideRequest request) {
        // 1. Call Python RAG to generate slide content
        JsonSlideResponse ragResponse = slideService.generateSlides(request);
        
        if (!"success".equals(ragResponse.getStatus())) {
            throw new RuntimeException("Failed to generate slides: " + ragResponse.getError());
        }
        
        // 2. Load PPTX template
        XMLSlideShow ppt = pptxService.loadTemplate("templates/education_template.pptx");
        
        // 3. Process each slide
        for (JsonSlideContent slide : ragResponse.getSlides()) {
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
                    
                case EXERCISE_SLIDE:
                    pptxService.addExerciseSlide(ppt, slide);
                    break;
            }
        }
        
        // 4. Return PPTX as bytes
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ppt.write(out);
        
        return ResponseEntity.ok()
            .header("Content-Disposition", "attachment; filename=presentation.pptx")
            .contentType(MediaType.APPLICATION_OCTET_STREAM)
            .body(out.toByteArray());
    }
}

// Template Service to map JSON to PPTX
@Service
public class PptxTemplateService {
    
    public void addContentSlide(XMLSlideShow ppt, JsonSlideContent slide) {
        XSLFSlide pptxSlide = ppt.createSlide();
        
        // Add title
        XSLFTextShape title = pptxSlide.createTextBox();
        title.setText(slide.getTitle());
        title.setAnchor(new Rectangle(50, 40, 600, 80));
        
        // Add content
        Object content = slide.getContent();
        if (content instanceof List) {
            // Bullet points
            XSLFTextShape textBox = pptxSlide.createTextBox();
            textBox.setAnchor(new Rectangle(50, 140, 600, 400));
            
            XSLFTextParagraph para = textBox.addNewTextParagraph();
            for (String item : (List<String>) content) {
                XSLFTextRun run = para.addNewTextRun();
                run.setText("• " + item);
                para.addLineBreak();
            }
        } else {
            // Plain text
            XSLFTextShape textBox = pptxSlide.createTextBox();
            textBox.setText(content.toString());
            textBox.setAnchor(new Rectangle(50, 140, 600, 400));
        }
    }
    
    public void addCodeSlide(XMLSlideShow ppt, JsonSlideContent slide) {
        XSLFSlide pptxSlide = ppt.createSlide();
        
        // Title
        XSLFTextShape title = pptxSlide.createTextBox();
        title.setText(slide.getTitle());
        
        // Code block with monospace font
        XSLFTextShape codeBox = pptxSlide.createTextBox();
        codeBox.setText(slide.getCode());
        codeBox.setAnchor(new Rectangle(50, 140, 600, 400));
        
        XSLFTextParagraph para = codeBox.getTextParagraphs().get(0);
        XSLFTextRun run = para.getTextRuns().get(0);
        run.setFontFamily("Courier New");
        run.setFontSize(12.0);
    }
}
"""
    
    print(java_code)
    print("\n" + "="*70)


if __name__ == "__main__":
    test_json_slide_generation()
    
    print("\n\n")
    print_spring_boot_example()
