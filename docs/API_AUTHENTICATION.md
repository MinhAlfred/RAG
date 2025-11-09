# API Key Authentication

This RAG API supports optional API key authentication to secure your endpoints.

## Configuration

### 1. Generate a Secure API Key

Generate a secure random API key using Python:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Example output:
```
8jK9mNpQrStUvWxYz0AbCdEfGhIjKlMnOpQrStUvWxYz
```

### 2. Configure in Python RAG Service

Add the API key to your `.env` file:

```env
# API Key for securing endpoints (optional)
RAG_API_KEY=8jK9mNpQrStUvWxYz0AbCdEfGhIjKlMnOpQrStUvWxYz
```

**Important Notes:**
- If `RAG_API_KEY` is **not set** or **empty**, API key authentication is **disabled**
- If `RAG_API_KEY` is set, **all protected endpoints** require the `X-API-Key` header
- Keep your API key secret and never commit it to version control

### 3. Configure in Spring Boot Service

Add the API key to your Spring Boot `application.yml` or `application.properties`:

**application.yml:**
```yaml
python:
  rag:
    api:
      url: http://localhost:8000
      key: 8jK9mNpQrStUvWxYz0AbCdEfGhIjKlMnOpQrStUvWxYz
```

**application.properties:**
```properties
python.rag.api.url=http://localhost:8000
python.rag.api.key=8jK9mNpQrStUvWxYz0AbCdEfGhIjKlMnOpQrStUvWxYz
```

## Protected Endpoints

The following endpoints require API key authentication:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ask` | POST | Question answering |
| `/ask/batch` | POST | Batch question processing |
| `/slides/generate` | POST | Slide generation (legacy) |
| `/slides/generate/json` | POST | Slide generation (JSON) |
| `/mindmap/generate` | POST | Mindmap generation |

## Public Endpoints

These endpoints are **always accessible** without authentication:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint |
| `/health` | GET | Health check |
| `/stats` | GET | System statistics |
| `/collections` | GET | List collections |
| `/question/types` | GET | List question types |
| `/slides/formats` | GET | List slide formats |
| `/docs` | GET | API documentation (Swagger) |
| `/redoc` | GET | API documentation (ReDoc) |

## Usage Examples

### Using cURL

```bash
# With API key
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 8jK9mNpQrStUvWxYz0AbCdEfGhIjKlMnOpQrStUvWxYz" \
  -d '{
    "question": "Máy tính là gì?",
    "grade_filter": 10,
    "return_sources": true
  }'
```

### Using Python Requests

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "8jK9mNpQrStUvWxYz0AbCdEfGhIjKlMnOpQrStUvWxYz"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

response = requests.post(
    f"{API_URL}/ask",
    headers=headers,
    json={
        "question": "Máy tính là gì?",
        "grade_filter": 10,
        "return_sources": True
    }
)

print(response.json())
```

### Using Spring Boot Feign Client

```java
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import feign.RequestInterceptor;
import org.springframework.context.annotation.Bean;
import org.springframework.beans.factory.annotation.Value;

@FeignClient(
    name = "python-rag-service",
    url = "${python.rag.api.url}",
    configuration = RagApiClient.RagApiConfiguration.class
)
public interface RagApiClient {

    @PostMapping("/ask")
    QuestionResponse ask(@RequestBody QuestionRequest request);

    @PostMapping("/mindmap/generate")
    MindmapResponse generateMindmap(@RequestBody MindmapRequest request);

    class RagApiConfiguration {
        @Value("${python.rag.api.key}")
        private String ragApiKey;

        @Bean
        public RequestInterceptor requestInterceptor() {
            return requestTemplate -> {
                requestTemplate.header("X-API-Key", ragApiKey);
            };
        }
    }
}
```

## Error Responses

### Missing API Key (401 Unauthorized)

```json
{
  "detail": "Missing API Key. Please provide X-API-Key header."
}
```

### Invalid API Key (403 Forbidden)

```json
{
  "detail": "Invalid API Key"
}
```

## Security Best Practices

1. **Use HTTPS in Production**: Always use HTTPS to encrypt API key transmission
2. **Rotate Keys Regularly**: Change your API key periodically
3. **Environment Variables**: Store API keys in environment variables, never in code
4. **Different Keys per Environment**: Use different API keys for dev/staging/production
5. **Monitor Access**: Log and monitor API access for unauthorized attempts
6. **Rate Limiting**: Consider adding rate limiting for additional security

## Disabling Authentication

To disable API key authentication for development or testing:

1. **Remove** or **comment out** the `RAG_API_KEY` in your `.env` file:
   ```env
   # RAG_API_KEY=
   ```

2. Restart the FastAPI service

3. All endpoints will be accessible without the `X-API-Key` header

**Warning**: Only disable authentication in development environments. Always use authentication in production.
