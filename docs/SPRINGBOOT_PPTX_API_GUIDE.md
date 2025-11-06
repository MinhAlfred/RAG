# PowerPoint Slide Generation API - Spring Boot Integration Guide

## Overview

This guide explains the JSON structure returned by the `/slides/generate/json` endpoint, specifically designed for **Apache POI** PPTX generation in Spring Boot applications.

## Table of Contents
- [Quick Start](#quick-start)
- [API Endpoint](#api-endpoint)
- [JSON Response Structure](#json-response-structure)
- [PowerPoint Layout Types](#powerpoint-layout-types)
- [Placeholder Types](#placeholder-types)
- [Working with Slides](#working-with-slides)
- [Apache POI Implementation Examples](#apache-poi-implementation-examples)

---

## Quick Start

### Request Example
```json
POST /slides/generate/json

{
  "topic": "Kiểu dữ liệu trong Python",
  "grade": 10,
  "slide_count": 5,
  "format": "json",
  "include_examples": true,
  "include_exercises": false
}
```

### Response Structure
```json
{
  "title": "Kiểu dữ liệu trong Python",
  "topic": "Kiểu dữ liệu trong Python",
  "grade": 10,
  "slides": [...],
  "metadata": {...},
  "status": "success",
  "processing_time": 2.5
}
```

---

## API Endpoint

**Endpoint:** `POST /slides/generate/json`

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | string | Yes | Slide topic/title |
| `grade` | integer | No | Grade level (3-12) |
| `slide_count` | integer | No | Number of slides (default: 5, max: 20) |
| `format` | string | Yes | Must be "json" |
| `include_examples` | boolean | No | Include code examples (default: true) |
| `include_exercises` | boolean | No | Include exercise slide (default: false) |
| `collection_name` | string | No | Vector DB collection name |

---

## JSON Response Structure

### Top Level Response
```typescript
{
  title: string;              // Presentation title
  topic: string;              // Topic name
  grade: number | null;       // Grade level
  slides: JsonSlideContent[]; // Array of slide objects
  metadata: JsonSlideMetadata; // Metadata
  status: string;             // "success" or "error"
  processing_time: number;    // Processing time in seconds
  error?: string;             // Error message (if status = "error")
}
```

### Metadata Object
```typescript
{
  total_slides: number;       // Total number of slides
  estimated_duration: string; // Estimated duration (e.g., "15 phút")
  sources: string[];          // Source references
  generated_at: string;       // ISO timestamp
  grade_level: string;        // Grade level label
}
```

---

## PowerPoint Layout Types

Each slide has a `layout` field that maps to Apache POI's `XSLFSlideLayout`:

| Layout Value | Apache POI Constant | Description |
|--------------|---------------------|-------------|
| `TITLE` | `SlideLayout.TITLE` | Title slide with centered title and subtitle |
| `TITLE_AND_CONTENT` | `SlideLayout.TITLE_AND_CONTENT` | Standard layout with title and body content |
| `SECTION_HEADER` | `SlideLayout.SECTION_HEADER` | Section divider slide |
| `TWO_CONTENT` | `SlideLayout.TWO_CONTENT` | Two-column layout |
| `COMPARISON` | `SlideLayout.COMPARISON` | Side-by-side comparison |
| `TITLE_ONLY` | `SlideLayout.TITLE_ONLY` | Only title, no content area |
| `BLANK` | `SlideLayout.BLANK` | Blank slide |
| `CONTENT_WITH_CAPTION` | `SlideLayout.CONTENT_WITH_CAPTION` | Content with caption below |
| `PICTURE_WITH_CAPTION` | `SlideLayout.PICTURE_WITH_CAPTION` | Picture with caption |

---

## Placeholder Types

Placeholders map directly to Apache POI's `Placeholder` enum:

| Placeholder Type | Apache POI Constant | Usage |
|------------------|---------------------|-------|
| `TITLE` | `Placeholder.TITLE` | Main slide title |
| `BODY` | `Placeholder.BODY` | Body content/bullet points |
| `CENTERED_TITLE` | `Placeholder.CENTERED_TITLE` | Centered title (title slides) |
| `SUBTITLE` | `Placeholder.SUBTITLE` | Subtitle text |
| `DATE` | `Placeholder.DATE` | Date field |
| `FOOTER` | `Placeholder.FOOTER` | Footer text |
| `SLIDE_NUMBER` | `Placeholder.SLIDE_NUMBER` | Slide number |
| `CONTENT` | `Placeholder.CONTENT` | Generic content |

---

## Working with Slides

### Slide Object Structure

Each slide in the `slides` array has the following structure:

```typescript
{
  // Basic Info
  slide_number: number;       // Slide number (1-indexed)
  type: string;              // Slide type (see below)
  layout: string;            // PowerPoint layout type

  // Placeholder-based Content (PRIMARY - Recommended for Apache POI)
  placeholders: [
    {
      placeholder_type: string;    // "TITLE", "BODY", etc.
      text_content?: string;       // Plain text for simple placeholders
      bullet_points?: BulletPoint[]; // Formatted bullets (only in placeholders)
      alignment: string;           // "LEFT", "CENTER", "RIGHT", "JUSTIFY"
    }
  ],

  // Legacy Simple Fields (for backward compatibility)
  title: string;                  // Slide title (also in placeholders)
  subtitle?: string;              // Subtitle (also in placeholders for title slides)
  content?: string[];             // Simple list of strings (same data as placeholders[].bullet_points but simplified)

  // Structured Content (for complex slides)
  code_block?: CodeBlock;         // Code snippet with formatting
  table?: TableData;              // Table structure
  images?: ImagePlaceholder[];    // Image placeholders

  // Metadata
  notes?: string;                 // Speaker notes
  key_points?: string[];          // Key takeaways
}
```

**Important Note:** Bullet points only appear **inside** `placeholders[].bullet_points`. The root-level `content` field contains a simplified string array version for backward compatibility.

### Slide Types

| Type | Description |
|------|-------------|
| `title_slide` | Opening title slide |
| `content_slide` | Standard content slide with bullets |
| `code_slide` | Slide with code snippet |
| `image_slide` | Slide with images |
| `table_slide` | Slide with table data |
| `exercise_slide` | Exercise/quiz slide |
| `summary_slide` | Summary/conclusion slide |

---

## Data Structures

### BulletPoint Object
```typescript
{
  text: string;        // Bullet point text
  level: number;       // Indent level (0-4)
                       // 0 = main bullet
                       // 1 = sub-bullet
                       // 2+ = deeper nesting
  bold: boolean;       // Bold formatting
  italic: boolean;     // Italic formatting
  font_size?: number;  // Font size (8-72pt)
}
```

### CodeBlock Object
```typescript
{
  code: string;              // Code snippet
  language: string;          // "python", "java", etc.
  font_family: string;       // Monospace font (e.g., "Courier New")
  font_size: number;         // Font size (8-24pt)
  highlight_lines?: number[]; // Lines to highlight
  position?: Position;       // X, Y, width, height in inches
}
```

### Position Object
```typescript
{
  x: number;      // X coordinate (inches)
  y: number;      // Y coordinate (inches)
  width: number;  // Width (inches)
  height: number; // Height (inches)
}
```

### ImagePlaceholder Object
```typescript
{
  placeholder_id: string;      // e.g., "{image1}"
  description: string;         // Image description
  suggested_search?: string;   // Search query for finding image
  position: Position;          // Position and size
  alt_text?: string;          // Accessibility text
}
```

### TableData Object
```typescript
{
  headers: string[];           // Column headers
  rows: TableCell[][];         // 2D array of cells
  position?: Position;         // Table position
  has_header_row: boolean;     // First row is header
}
```

### TableCell Object
```typescript
{
  text: string;               // Cell text
  bold: boolean;              // Bold text
  background_color?: string;  // Hex color (e.g., "#FFCC00")
  align: string;             // "LEFT", "CENTER", "RIGHT", "JUSTIFY"
}
```

---

## Apache POI Implementation Examples

### Example 1: Creating a Title Slide

**JSON Input:**
```json
{
  "slide_number": 1,
  "type": "title_slide",
  "layout": "TITLE",
  "placeholders": [
    {
      "placeholder_type": "TITLE",
      "text_content": "Python Data Types",
      "alignment": "CENTER"
    },
    {
      "placeholder_type": "SUBTITLE",
      "text_content": "Grade 10 - Computer Science",
      "alignment": "CENTER"
    }
  ],
  "title": "Python Data Types",
  "subtitle": "Grade 10 - Computer Science"
}
```

**Java/Spring Boot (Apache POI):**
```java
import org.apache.poi.xslf.usermodel.*;

public XSLFSlide createTitleSlide(XMLSlideShow ppt, JsonNode slideData) {
    // Get TITLE layout
    XSLFSlideMaster master = ppt.getSlideMasters().get(0);
    XSLFSlideLayout titleLayout = master.getLayout(SlideLayout.TITLE);
    XSLFSlide slide = ppt.createSlide(titleLayout);

    // Process placeholders
    JsonNode placeholders = slideData.get("placeholders");
    for (JsonNode placeholder : placeholders) {
        String type = placeholder.get("placeholder_type").asText();
        String text = placeholder.get("text_content").asText();
        String alignment = placeholder.get("alignment").asText();

        // Find and fill placeholder
        for (XSLFShape shape : slide.getShapes()) {
            if (shape instanceof XSLFTextShape) {
                XSLFTextShape textShape = (XSLFTextShape) shape;
                Placeholder ph = textShape.getPlaceholder();

                if (ph != null && ph.name().equals(type)) {
                    textShape.clearText();
                    XSLFTextParagraph paragraph = textShape.addNewTextParagraph();
                    XSLFTextRun run = paragraph.addNewTextRun();
                    run.setText(text);

                    // Set alignment
                    if ("CENTER".equals(alignment)) {
                        paragraph.setTextAlign(TextAlign.CENTER);
                    }
                }
            }
        }
    }

    return slide;
}
```

### Example 2: Creating a Content Slide with Bullets

**JSON Input:**
```json
{
  "slide_number": 2,
  "type": "content_slide",
  "layout": "TITLE_AND_CONTENT",
  "placeholders": [
    {
      "placeholder_type": "TITLE",
      "text_content": "Basic Data Types",
      "alignment": "LEFT"
    },
    {
      "placeholder_type": "BODY",
      "bullet_points": [
        {"text": "int: Integer numbers", "level": 0, "bold": true, "font_size": 18},
        {"text": "float: Floating point numbers", "level": 1, "bold": false, "font_size": 16},
        {"text": "str: Text strings", "level": 1, "bold": false, "font_size": 16}
      ],
      "alignment": "LEFT"
    }
  ]
}
```

**Java/Spring Boot (Apache POI):**
```java
public XSLFSlide createContentSlide(XMLSlideShow ppt, JsonNode slideData) {
    XSLFSlideMaster master = ppt.getSlideMasters().get(0);
    XSLFSlideLayout contentLayout = master.getLayout(SlideLayout.TITLE_AND_CONTENT);
    XSLFSlide slide = ppt.createSlide(contentLayout);

    JsonNode placeholders = slideData.get("placeholders");
    for (JsonNode placeholder : placeholders) {
        String type = placeholder.get("placeholder_type").asText();

        if ("TITLE".equals(type)) {
            // Set title
            String title = placeholder.get("text_content").asText();
            slide.getPlaceholder(0).setText(title);
        }
        else if ("BODY".equals(type)) {
            // Set bullet points
            XSLFTextShape bodyShape = slide.getPlaceholder(1);
            bodyShape.clearText();

            JsonNode bullets = placeholder.get("bullet_points");
            for (JsonNode bullet : bullets) {
                String text = bullet.get("text").asText();
                int level = bullet.get("level").asInt();
                boolean bold = bullet.get("bold").asBoolean();
                int fontSize = bullet.get("font_size").asInt();

                XSLFTextParagraph paragraph = bodyShape.addNewTextParagraph();
                paragraph.setIndentLevel(level);
                paragraph.setBullet(true);

                XSLFTextRun run = paragraph.addNewTextRun();
                run.setText(text);
                run.setFontSize((double) fontSize);
                run.setBold(bold);
            }
        }
    }

    return slide;
}
```

### Example 3: Creating a Code Slide

**JSON Input:**
```json
{
  "slide_number": 3,
  "type": "code_slide",
  "layout": "TITLE_AND_CONTENT",
  "title": "Example Code",
  "code_block": {
    "code": "x = 10\ny = 20\nprint(x + y)",
    "language": "python",
    "font_family": "Courier New",
    "font_size": 12,
    "position": {"x": 1.0, "y": 2.5, "width": 8.5, "height": 4.0}
  }
}
```

**Java/Spring Boot (Apache POI):**
```java
public XSLFSlide createCodeSlide(XMLSlideShow ppt, JsonNode slideData) {
    XSLFSlideMaster master = ppt.getSlideMasters().get(0);
    XSLFSlideLayout layout = master.getLayout(SlideLayout.TITLE_AND_CONTENT);
    XSLFSlide slide = ppt.createSlide(layout);

    // Set title
    String title = slideData.get("title").asText();
    slide.getPlaceholder(0).setText(title);

    // Create code text box
    JsonNode codeBlock = slideData.get("code_block");
    String code = codeBlock.get("code").asText();
    String fontFamily = codeBlock.get("font_family").asText();
    int fontSize = codeBlock.get("font_size").asInt();

    JsonNode position = codeBlock.get("position");
    double x = position.get("x").asDouble() * 72; // Convert inches to points
    double y = position.get("y").asDouble() * 72;
    double width = position.get("width").asDouble() * 72;
    double height = position.get("height").asDouble() * 72;

    // Create text box for code
    XSLFTextBox codeBox = slide.createTextBox();
    codeBox.setAnchor(new Rectangle2D.Double(x, y, width, height));

    XSLFTextParagraph paragraph = codeBox.addNewTextParagraph();
    XSLFTextRun run = paragraph.addNewTextRun();
    run.setText(code);
    run.setFontFamily(fontFamily);
    run.setFontSize((double) fontSize);

    // Optional: Set background color for code block
    codeBox.setFillColor(new Color(240, 240, 240));

    return slide;
}
```

### Example 4: Utility Method to Process All Slides

**Java/Spring Boot:**
```java
@Service
public class PowerPointService {

    public ByteArrayOutputStream generatePowerPoint(JsonNode responseData) throws IOException {
        XMLSlideShow ppt = new XMLSlideShow();

        JsonNode slides = responseData.get("slides");
        for (JsonNode slideData : slides) {
            String type = slideData.get("type").asText();
            String layout = slideData.get("layout").asText();

            switch (type) {
                case "title_slide":
                    createTitleSlide(ppt, slideData);
                    break;
                case "content_slide":
                    createContentSlide(ppt, slideData);
                    break;
                case "code_slide":
                    createCodeSlide(ppt, slideData);
                    break;
                case "exercise_slide":
                    createExerciseSlide(ppt, slideData);
                    break;
                default:
                    createGenericSlide(ppt, slideData);
            }
        }

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ppt.write(out);
        ppt.close();

        return out;
    }
}
```

---

## Best Practices

### 1. Always Check for Null/Optional Fields
```java
// Check if code_block exists
if (slideData.has("code_block") && !slideData.get("code_block").isNull()) {
    JsonNode codeBlock = slideData.get("code_block");
    // Process code block
}

// Check if bullet_points exist
if (placeholder.has("bullet_points")) {
    JsonNode bullets = placeholder.get("bullet_points");
    // Process bullets
}
```

### 2. Use Placeholder-Based Approach (Recommended)

The `placeholders` array provides the most structured way to work with Apache POI:

```java
// Modern approach using placeholders
JsonNode placeholders = slideData.get("placeholders");
for (JsonNode placeholder : placeholders) {
    String placeholderType = placeholder.get("placeholder_type").asText();
    // Use placeholderType to find the correct Apache POI placeholder
    XSLFTextShape shape = findPlaceholder(slide, placeholderType);
    // Fill placeholder with content
}
```

### 3. Handle Legacy Fields for Backward Compatibility

Some fields are marked as `[Deprecated]` but kept for compatibility:

```java
// New way (preferred)
if (slideData.has("code_block")) {
    JsonNode codeBlock = slideData.get("code_block");
    String code = codeBlock.get("code").asText();
}
// Old way (fallback)
else if (slideData.has("code")) {
    String code = slideData.get("code").asText();
}
```

### 4. Position Conversion (Inches to Points)

Apache POI uses points (1/72 inch), but JSON provides inches:

```java
// Convert position from inches to points
JsonNode position = codeBlock.get("position");
double xPoints = position.get("x").asDouble() * 72.0;
double yPoints = position.get("y").asDouble() * 72.0;
double widthPoints = position.get("width").asDouble() * 72.0;
double heightPoints = position.get("height").asDouble() * 72.0;

Rectangle2D.Double anchor = new Rectangle2D.Double(xPoints, yPoints, widthPoints, heightPoints);
textBox.setAnchor(anchor);
```

### 5. Text Alignment Mapping

```java
public TextAlign mapAlignment(String alignment) {
    switch (alignment) {
        case "CENTER": return TextAlign.CENTER;
        case "RIGHT": return TextAlign.RIGHT;
        case "JUSTIFY": return TextAlign.JUSTIFY;
        case "LEFT":
        default: return TextAlign.LEFT;
    }
}
```

---

## Complete Example: Full Integration

```java
@RestController
@RequestMapping("/api/presentations")
public class PresentationController {

    @Autowired
    private RestTemplate restTemplate;

    @PostMapping("/generate")
    public ResponseEntity<byte[]> generatePresentation(@RequestBody SlideRequest request) {
        // Call Python RAG API
        String pythonApiUrl = "http://localhost:8000/slides/generate/json";
        ResponseEntity<JsonNode> response = restTemplate.postForEntity(
            pythonApiUrl,
            request,
            JsonNode.class
        );

        JsonNode responseData = response.getBody();

        // Generate PowerPoint using Apache POI
        try {
            ByteArrayOutputStream pptxStream = powerPointService.generatePowerPoint(responseData);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.parseMediaType("application/vnd.openxmlformats-officedocument.presentationml.presentation"));
            headers.setContentDispositionFormData("attachment", "presentation.pptx");

            return ResponseEntity.ok()
                .headers(headers)
                .body(pptxStream.toByteArray());

        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
```

---

## Troubleshooting

### Common Issues

1. **Placeholder Not Found**
   - Make sure you're using the correct placeholder type
   - Some layouts may not have all placeholder types
   - Use `slide.getShapes()` to debug available shapes

2. **Text Not Appearing**
   - Call `clearText()` before adding new text
   - Ensure you're adding text to the correct shape

3. **Formatting Not Applied**
   - Set formatting on `XSLFTextRun`, not `XSLFTextParagraph`
   - Font size is in double, not int

4. **Position Issues**
   - Remember to convert inches to points (multiply by 72)
   - Check coordinate system (origin is top-left)

---

## Additional Resources

- [Apache POI XSLF Documentation](https://poi.apache.org/components/slideshow/)
- [PowerPoint Slide Layouts Reference](https://poi.apache.org/apidocs/dev/org/apache/poi/xslf/usermodel/SlideLayout.html)
- [Placeholder Types Reference](https://poi.apache.org/apidocs/dev/org/apache/poi/sl/usermodel/Placeholder.html)

---

## Support

For questions or issues:
- Check the API response for error messages
- Verify your request matches the schema
- Test with the example JSON provided above

**API Version:** 1.0.0
**Last Updated:** 2025-01-07
