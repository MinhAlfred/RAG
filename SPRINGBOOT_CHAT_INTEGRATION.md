# Spring Boot Integration Guide - Chat & Conversation API

Complete guide for integrating the RAG Chat API with Spring Boot applications.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [API Authentication](#api-authentication)
4. [API Endpoints Reference](#api-endpoints-reference)
5. [Spring Boot Implementation](#spring-boot-implementation)
6. [Best Practices](#best-practices)
7. [Error Handling](#error-handling)
8. [Examples](#examples)

## Overview

The RAG Chat API provides conversation management with memory and context-aware AI responses. This guide shows how to integrate it with Spring Boot applications.

### Key Features
- **Conversation Management**: Create, list, update, and delete conversations
- **Contextual Chat**: AI responses with conversation history memory
- **Source Citations**: Optional source documents for answers
- **Pagination**: Efficient list operations
- **User Isolation**: Each user has separate conversations

### Base URL
```
http://localhost:8000/api/v1/chat
```

## Quick Start

### 1. Add Dependencies

Add to `pom.xml`:
```xml
<dependencies>
    <!-- Spring Web -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>

    <!-- WebClient (Recommended) -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-webflux</artifactId>
    </dependency>

    <!-- Lombok (Optional but recommended) -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <optional>true</optional>
    </dependency>
</dependencies>
```

### 2. Configure Application Properties

`application.yml`:
```yaml
rag:
  api:
    base-url: http://localhost:8000/api/v1
    api-key: ${RAG_API_KEY:your-api-key-here}
    timeout: 30000  # 30 seconds

spring:
  application:
    name: your-spring-app
```

### 3. Create Configuration Class

```java
@Configuration
public class RagApiConfig {

    @Value("${rag.api.base-url}")
    private String baseUrl;

    @Value("${rag.api.api-key}")
    private String apiKey;

    @Value("${rag.api.timeout:30000}")
    private int timeout;

    @Bean
    public WebClient ragWebClient() {
        return WebClient.builder()
            .baseUrl(baseUrl)
            .defaultHeader("X-API-Key", apiKey)
            .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
            .build();
    }
}
```

## API Authentication

### API Key Header
All requests require the `X-API-Key` header:

```http
X-API-Key: your-api-key-here
```

### Configure in Environment
```bash
# .env file
RAG_API_KEY=your-api-key-here
```

## API Endpoints Reference

### Conversation Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat/conversations` | Create new conversation |
| GET | `/chat/conversations` | List user conversations |
| GET | `/chat/conversations/{id}` | Get specific conversation |
| PATCH | `/chat/conversations/{id}` | Update conversation |
| DELETE | `/chat/conversations/{id}` | Delete conversation |

### Message Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat/messages` | Send message and get AI response |
| GET | `/chat/conversations/{id}/messages` | Get conversation messages |

## Spring Boot Implementation

### 1. Data Transfer Objects (DTOs)

```java
package com.example.dto;

import lombok.Data;
import lombok.Builder;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

// ========== Request DTOs ==========

@Data
@Builder
public class ConversationCreateRequest {
    private String userId;
    private String title;  // Optional
}

@Data
@Builder
public class ConversationUpdateRequest {
    private String title;
    private Integer grade;
    private Boolean isArchived;
}

@Data
@Builder
public class ChatMessageRequest {
    private String conversationId;  // Optional - creates new if omitted
    private String userId;
    private String message;
    private Integer grade;
    private Boolean returnSources;
    private Integer maxHistory;

    public static ChatMessageRequest createNew(String userId, String message) {
        return ChatMessageRequest.builder()
            .userId(userId)
            .message(message)
            .returnSources(true)
            .maxHistory(10)
            .build();
    }
}

// ========== Response DTOs ==========

@Data
public class ConversationResponse {
    private String id;
    private String userId;
    private String title;
    private Integer grade;
    private String subject;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private Boolean isArchived;
    private Map<String, Object> metadata;
    private Integer messageCount;
}

@Data
public class ChatMessageResponse {
    private String id;
    private String conversationId;
    private String role;  // "user" or "assistant"
    private String content;
    private List<Map<String, Object>> sources;
    private String retrievalMode;
    private Integer docsRetrieved;
    private Boolean webSearchUsed;
    private Integer processingTime;
    private LocalDateTime createdAt;
    private Map<String, Object> metadata;
}

@Data
public class ChatResponse {
    private String conversationId;
    private String messageId;
    private ChatMessageResponse userMessage;
    private ChatMessageResponse assistantMessage;
    private String status;
    private String error;
}

@Data
public class ConversationListResponse {
    private List<ConversationResponse> conversations;
    private Integer total;
    private Integer page;
    private Integer pageSize;
}

@Data
public class ConversationWithMessagesResponse {
    private ConversationResponse conversation;
    private List<ChatMessageResponse> messages;
    private Integer totalMessages;
}

@Data
public class DeleteResponse {
    private Boolean success;
    private String message;
    private String deletedId;
}
```

### 2. Service Implementation

```java
package com.example.service;

import com.example.dto.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Slf4j
@Service
@RequiredArgsConstructor
public class RagChatService {

    private final WebClient ragWebClient;

    // ========== Conversation Management ==========

    /**
     * Create a new conversation
     */
    public Mono<ConversationResponse> createConversation(String userId, String title) {
        ConversationCreateRequest request = ConversationCreateRequest.builder()
            .userId(userId)
            .title(title)
            .build();

        return ragWebClient.post()
            .uri("/chat/conversations")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(ConversationResponse.class)
            .doOnSuccess(response -> log.info("Created conversation: {}", response.getId()))
            .doOnError(error -> log.error("Failed to create conversation", error));
    }

    /**
     * Create conversation with minimal info (auto-generated title)
     */
    public Mono<ConversationResponse> createConversation(String userId) {
        return createConversation(userId, null);
    }

    /**
     * List user conversations with pagination
     */
    public Mono<ConversationListResponse> listConversations(
            String userId,
            int page,
            int pageSize,
            boolean includeArchived) {

        return ragWebClient.get()
            .uri(uriBuilder -> uriBuilder
                .path("/chat/conversations")
                .queryParam("user_id", userId)
                .queryParam("page", page)
                .queryParam("page_size", pageSize)
                .queryParam("include_archived", includeArchived)
                .build())
            .retrieve()
            .bodyToMono(ConversationListResponse.class);
    }

    /**
     * Get specific conversation
     */
    public Mono<ConversationResponse> getConversation(String conversationId, String userId) {
        return ragWebClient.get()
            .uri(uriBuilder -> uriBuilder
                .path("/chat/conversations/{id}")
                .queryParam("user_id", userId)
                .build(conversationId))
            .retrieve()
            .bodyToMono(ConversationResponse.class);
    }

    /**
     * Update conversation
     */
    public Mono<ConversationResponse> updateConversation(
            String conversationId,
            String userId,
            ConversationUpdateRequest updateRequest) {

        return ragWebClient.patch()
            .uri(uriBuilder -> uriBuilder
                .path("/chat/conversations/{id}")
                .queryParam("user_id", userId)
                .build(conversationId))
            .bodyValue(updateRequest)
            .retrieve()
            .bodyToMono(ConversationResponse.class);
    }

    /**
     * Delete conversation
     */
    public Mono<DeleteResponse> deleteConversation(String conversationId, String userId) {
        return ragWebClient.delete()
            .uri(uriBuilder -> uriBuilder
                .path("/chat/conversations/{id}")
                .queryParam("user_id", userId)
                .build(conversationId))
            .retrieve()
            .bodyToMono(DeleteResponse.class);
    }

    // ========== Message Management ==========

    /**
     * Send message and get AI response
     */
    public Mono<ChatResponse> sendMessage(ChatMessageRequest request) {
        return ragWebClient.post()
            .uri("/chat/messages")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(ChatResponse.class)
            .doOnSuccess(response -> log.info(
                "Message sent to conversation: {} (processing_time={}ms)",
                response.getConversationId(),
                response.getAssistantMessage().getProcessingTime()
            ));
    }

    /**
     * Send message to existing conversation
     */
    public Mono<ChatResponse> sendMessage(
            String conversationId,
            String userId,
            String message) {

        ChatMessageRequest request = ChatMessageRequest.builder()
            .conversationId(conversationId)
            .userId(userId)
            .message(message)
            .returnSources(true)
            .maxHistory(10)
            .build();

        return sendMessage(request);
    }

    /**
     * Start new conversation with first message
     */
    public Mono<ChatResponse> startNewConversation(String userId, String message) {
        ChatMessageRequest request = ChatMessageRequest.builder()
            .userId(userId)
            .message(message)
            .returnSources(true)
            .maxHistory(10)
            .build();

        return sendMessage(request);
    }

    /**
     * Get conversation messages
     */
    public Mono<ConversationWithMessagesResponse> getConversationMessages(
            String conversationId,
            String userId,
            Integer limit) {

        return ragWebClient.get()
            .uri(uriBuilder -> {
                var builder = uriBuilder
                    .path("/chat/conversations/{id}/messages")
                    .queryParam("user_id", userId);
                if (limit != null) {
                    builder.queryParam("limit", limit);
                }
                return builder.build(conversationId);
            })
            .retrieve()
            .bodyToMono(ConversationWithMessagesResponse.class);
    }
}
```

### 3. REST Controller

```java
package com.example.controller;

import com.example.dto.*;
import com.example.service.RagChatService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
public class ChatController {

    private final RagChatService ragChatService;

    /**
     * Create new conversation
     * POST /api/chat/conversations
     */
    @PostMapping("/conversations")
    public Mono<ResponseEntity<ConversationResponse>> createConversation(
            @RequestParam String userId,
            @RequestParam(required = false) String title) {

        return ragChatService.createConversation(userId, title)
            .map(ResponseEntity::ok);
    }

    /**
     * List user conversations
     * GET /api/chat/conversations?userId=user123&page=1&pageSize=20
     */
    @GetMapping("/conversations")
    public Mono<ResponseEntity<ConversationListResponse>> listConversations(
            @RequestParam String userId,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize,
            @RequestParam(defaultValue = "false") boolean includeArchived) {

        return ragChatService.listConversations(userId, page, pageSize, includeArchived)
            .map(ResponseEntity::ok);
    }

    /**
     * Get specific conversation
     * GET /api/chat/conversations/{id}?userId=user123
     */
    @GetMapping("/conversations/{id}")
    public Mono<ResponseEntity<ConversationResponse>> getConversation(
            @PathVariable String id,
            @RequestParam String userId) {

        return ragChatService.getConversation(id, userId)
            .map(ResponseEntity::ok);
    }

    /**
     * Update conversation
     * PATCH /api/chat/conversations/{id}?userId=user123
     */
    @PatchMapping("/conversations/{id}")
    public Mono<ResponseEntity<ConversationResponse>> updateConversation(
            @PathVariable String id,
            @RequestParam String userId,
            @RequestBody ConversationUpdateRequest request) {

        return ragChatService.updateConversation(id, userId, request)
            .map(ResponseEntity::ok);
    }

    /**
     * Delete conversation
     * DELETE /api/chat/conversations/{id}?userId=user123
     */
    @DeleteMapping("/conversations/{id}")
    public Mono<ResponseEntity<DeleteResponse>> deleteConversation(
            @PathVariable String id,
            @RequestParam String userId) {

        return ragChatService.deleteConversation(id, userId)
            .map(ResponseEntity::ok);
    }

    /**
     * Send message to conversation
     * POST /api/chat/messages
     */
    @PostMapping("/messages")
    public Mono<ResponseEntity<ChatResponse>> sendMessage(
            @RequestBody ChatMessageRequest request) {

        return ragChatService.sendMessage(request)
            .map(ResponseEntity::ok);
    }

    /**
     * Get conversation messages
     * GET /api/chat/conversations/{id}/messages?userId=user123&limit=50
     */
    @GetMapping("/conversations/{id}/messages")
    public Mono<ResponseEntity<ConversationWithMessagesResponse>> getMessages(
            @PathVariable String id,
            @RequestParam String userId,
            @RequestParam(required = false) Integer limit) {

        return ragChatService.getConversationMessages(id, userId, limit)
            .map(ResponseEntity::ok);
    }
}
```

### 4. Alternative: Synchronous Implementation (RestTemplate)

For non-reactive applications:

```java
package com.example.service;

import com.example.dto.*;
import lombok.RequiredArgsConstructor;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

@Service
@RequiredArgsConstructor
public class RagChatServiceSync {

    private final RestTemplate restTemplate;
    private final String baseUrl = "http://localhost:8000/api/v1";
    private final String apiKey;  // Inject from properties

    private HttpHeaders createHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.set("X-API-Key", apiKey);
        headers.setContentType(MediaType.APPLICATION_JSON);
        return headers;
    }

    /**
     * Create conversation (synchronous)
     */
    public ConversationResponse createConversation(String userId, String title) {
        ConversationCreateRequest request = ConversationCreateRequest.builder()
            .userId(userId)
            .title(title)
            .build();

        HttpEntity<ConversationCreateRequest> entity =
            new HttpEntity<>(request, createHeaders());

        ResponseEntity<ConversationResponse> response = restTemplate.exchange(
            baseUrl + "/chat/conversations",
            HttpMethod.POST,
            entity,
            ConversationResponse.class
        );

        return response.getBody();
    }

    /**
     * Send message (synchronous)
     */
    public ChatResponse sendMessage(ChatMessageRequest request) {
        HttpEntity<ChatMessageRequest> entity =
            new HttpEntity<>(request, createHeaders());

        ResponseEntity<ChatResponse> response = restTemplate.exchange(
            baseUrl + "/chat/messages",
            HttpMethod.POST,
            entity,
            ChatResponse.class
        );

        return response.getBody();
    }

    /**
     * List conversations (synchronous)
     */
    public ConversationListResponse listConversations(
            String userId, int page, int pageSize, boolean includeArchived) {

        String url = UriComponentsBuilder.fromHttpUrl(baseUrl + "/chat/conversations")
            .queryParam("user_id", userId)
            .queryParam("page", page)
            .queryParam("page_size", pageSize)
            .queryParam("include_archived", includeArchived)
            .toUriString();

        HttpEntity<?> entity = new HttpEntity<>(createHeaders());

        ResponseEntity<ConversationListResponse> response = restTemplate.exchange(
            url,
            HttpMethod.GET,
            entity,
            ConversationListResponse.class
        );

        return response.getBody();
    }
}
```

## Best Practices

### 1. Connection Pooling

Configure connection pool for better performance:

```java
@Bean
public WebClient ragWebClient() {
    ConnectionProvider provider = ConnectionProvider.builder("rag-pool")
        .maxConnections(100)
        .maxIdleTime(Duration.ofSeconds(20))
        .maxLifeTime(Duration.ofSeconds(60))
        .build();

    HttpClient httpClient = HttpClient.create(provider)
        .responseTimeout(Duration.ofSeconds(30));

    return WebClient.builder()
        .baseUrl(baseUrl)
        .defaultHeader("X-API-Key", apiKey)
        .clientConnector(new ReactorClientHttpConnector(httpClient))
        .build();
}
```

### 2. Error Handling

Implement robust error handling:

```java
public Mono<ChatResponse> sendMessageWithErrorHandling(ChatMessageRequest request) {
    return ragWebClient.post()
        .uri("/chat/messages")
        .bodyValue(request)
        .retrieve()
        .onStatus(
            HttpStatus::is4xxClientError,
            response -> response.bodyToMono(String.class)
                .flatMap(body -> Mono.error(
                    new ChatApiException("Client error: " + body)
                ))
        )
        .onStatus(
            HttpStatus::is5xxServerError,
            response -> Mono.error(
                new ChatApiException("Server error")
            )
        )
        .bodyToMono(ChatResponse.class)
        .timeout(Duration.ofSeconds(30))
        .retry(3)  // Retry up to 3 times
        .onErrorResume(e -> {
            log.error("Failed to send message", e);
            return Mono.empty();
        });
}
```

### 3. Caching

Cache conversation lists to reduce API calls:

```java
@Cacheable(value = "conversations", key = "#userId + '_' + #page")
public Mono<ConversationListResponse> listConversations(
        String userId, int page, int pageSize, boolean includeArchived) {
    // ... implementation
}

@CacheEvict(value = "conversations", allEntries = true)
public Mono<ConversationResponse> createConversation(String userId, String title) {
    // ... implementation
}
```

### 4. Async Processing

For long-running operations:

```java
@Async
public CompletableFuture<ChatResponse> sendMessageAsync(
        String conversationId, String userId, String message) {

    ChatResponse response = sendMessageSync(conversationId, userId, message);
    return CompletableFuture.completedFuture(response);
}
```

### 5. User Context

Extract user ID from security context:

```java
@Service
public class ChatService {

    @Autowired
    private RagChatService ragChatService;

    private String getCurrentUserId() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return auth.getName();  // Or extract from custom UserDetails
    }

    public Mono<ConversationResponse> createMyConversation(String title) {
        String userId = getCurrentUserId();
        return ragChatService.createConversation(userId, title);
    }
}
```

## Error Handling

### Common Errors

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing API key |
| 404 | Not Found | Conversation/message not found |
| 422 | Validation Error | Invalid request parameters |
| 500 | Internal Server Error | Server-side error |

### Custom Exception Handler

```java
@RestControllerAdvice
public class ChatApiExceptionHandler {

    @ExceptionHandler(ChatApiException.class)
    public ResponseEntity<ErrorResponse> handleChatApiException(ChatApiException ex) {
        ErrorResponse error = ErrorResponse.builder()
            .status(HttpStatus.BAD_REQUEST.value())
            .message(ex.getMessage())
            .timestamp(LocalDateTime.now())
            .build();

        return ResponseEntity.badRequest().body(error);
    }

    @ExceptionHandler(WebClientResponseException.class)
    public ResponseEntity<ErrorResponse> handleWebClientException(
            WebClientResponseException ex) {

        ErrorResponse error = ErrorResponse.builder()
            .status(ex.getStatusCode().value())
            .message(ex.getResponseBodyAsString())
            .timestamp(LocalDateTime.now())
            .build();

        return ResponseEntity.status(ex.getStatusCode()).body(error);
    }
}

@Data
@Builder
class ErrorResponse {
    private int status;
    private String message;
    private LocalDateTime timestamp;
}
```

## Examples

### Example 1: Complete Chat Flow

```java
@Service
public class ChatFlowExample {

    @Autowired
    private RagChatService chatService;

    public void demonstrateChatFlow(String userId) {
        // 1. Create new conversation
        ConversationResponse conversation = chatService
            .createConversation(userId, "Learning Python")
            .block();

        String conversationId = conversation.getId();

        // 2. Send first message
        ChatResponse response1 = chatService
            .sendMessage(conversationId, userId, "What is a variable?")
            .block();

        System.out.println("AI: " + response1.getAssistantMessage().getContent());

        // 3. Send follow-up message (with context)
        ChatResponse response2 = chatService
            .sendMessage(conversationId, userId, "Can you give me an example?")
            .block();

        System.out.println("AI: " + response2.getAssistantMessage().getContent());

        // 4. Get all messages
        ConversationWithMessagesResponse history = chatService
            .getConversationMessages(conversationId, userId, null)
            .block();

        System.out.println("Total messages: " + history.getTotalMessages());

        // 5. Archive conversation
        ConversationUpdateRequest update = ConversationUpdateRequest.builder()
            .isArchived(true)
            .build();

        chatService.updateConversation(conversationId, userId, update).block();
    }
}
```

### Example 2: Batch Operations

```java
public void batchCreateConversations(List<String> userIds) {
    List<Mono<ConversationResponse>> operations = userIds.stream()
        .map(userId -> chatService.createConversation(userId))
        .collect(Collectors.toList());

    Flux.merge(operations)
        .subscribe(
            response -> log.info("Created: {}", response.getId()),
            error -> log.error("Error: ", error),
            () -> log.info("All conversations created")
        );
}
```

### Example 3: Pagination

```java
public List<ConversationResponse> getAllUserConversations(String userId) {
    List<ConversationResponse> allConversations = new ArrayList<>();
    int page = 1;
    int pageSize = 20;

    while (true) {
        ConversationListResponse response = chatService
            .listConversations(userId, page, pageSize, false)
            .block();

        allConversations.addAll(response.getConversations());

        if (allConversations.size() >= response.getTotal()) {
            break;
        }
        page++;
    }

    return allConversations;
}
```

### Example 4: WebSocket Integration

For real-time chat updates:

```java
@Controller
public class ChatWebSocketController {

    @Autowired
    private RagChatService chatService;

    @MessageMapping("/chat.send")
    @SendTo("/topic/messages/{conversationId}")
    public ChatResponse handleChatMessage(
            @DestinationVariable String conversationId,
            ChatMessageRequest request) {

        return chatService.sendMessage(request).block();
    }
}
```

## Database Schema Reference

The chat API uses the following PostgreSQL tables:

### Conversations Table
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    title VARCHAR,
    grade INTEGER,
    subject VARCHAR DEFAULT 'Tin Học',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_archived BOOLEAN DEFAULT FALSE,
    metadata JSONB
);
```

### Chat Messages Table
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    sources JSONB,
    retrieval_mode VARCHAR,
    docs_retrieved INTEGER,
    web_search_used BOOLEAN,
    processing_time INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);
```

## Performance Optimization

### 1. Request Timeout Configuration
```yaml
rag:
  api:
    timeout:
      connect: 5000      # Connection timeout: 5s
      read: 30000        # Read timeout: 30s
      write: 10000       # Write timeout: 10s
```

### 2. Circuit Breaker Pattern

Using Resilience4j:

```java
@Configuration
public class ResilienceConfig {

    @Bean
    public CircuitBreakerRegistry circuitBreakerRegistry() {
        CircuitBreakerConfig config = CircuitBreakerConfig.custom()
            .failureRateThreshold(50)
            .waitDurationInOpenState(Duration.ofSeconds(30))
            .slidingWindowSize(10)
            .build();

        return CircuitBreakerRegistry.of(config);
    }
}

@Service
public class ResilientChatService {

    @CircuitBreaker(name = "ragChat", fallbackMethod = "fallbackSendMessage")
    public Mono<ChatResponse> sendMessage(ChatMessageRequest request) {
        return ragChatService.sendMessage(request);
    }

    private Mono<ChatResponse> fallbackSendMessage(
            ChatMessageRequest request, Exception ex) {
        log.warn("Circuit breaker activated, returning cached response");
        return Mono.just(getCachedResponse(request));
    }
}
```

## Testing

### Unit Test Example

```java
@ExtendWith(MockitoExtension.class)
class RagChatServiceTest {

    @Mock
    private WebClient webClient;

    @Mock
    private WebClient.RequestBodyUriSpec requestBodyUriSpec;

    @Mock
    private WebClient.ResponseSpec responseSpec;

    @InjectMocks
    private RagChatService chatService;

    @Test
    void testCreateConversation() {
        // Given
        ConversationResponse expected = new ConversationResponse();
        expected.setId("conv-123");

        when(webClient.post()).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.uri(anyString())).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.bodyValue(any())).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.retrieve()).thenReturn(responseSpec);
        when(responseSpec.bodyToMono(ConversationResponse.class))
            .thenReturn(Mono.just(expected));

        // When
        ConversationResponse result = chatService
            .createConversation("user123", "Test")
            .block();

        // Then
        assertNotNull(result);
        assertEquals("conv-123", result.getId());
    }
}
```

## Additional Resources

- [RAG API Documentation](http://localhost:8000/docs)
- [Spring WebClient Guide](https://docs.spring.io/spring-framework/reference/web/webflux-webclient.html)
- [Spring WebFlux Documentation](https://docs.spring.io/spring-framework/reference/web/webflux.html)

## Troubleshooting

### Issue: Connection Timeout

**Solution:**
```yaml
rag:
  api:
    timeout: 60000  # Increase to 60 seconds
```

### Issue: 401 Unauthorized

**Solution:** Verify API key is correctly configured:
```bash
curl -H "X-API-Key: your-key" http://localhost:8000/health
```

### Issue: Memory Issues with Large Conversations

**Solution:** Use pagination when retrieving messages:
```java
getConversationMessages(conversationId, userId, 50);  // Limit to 50 messages
```

---

**Happy Integrating!** For questions or issues, check the API documentation at `/docs`.
