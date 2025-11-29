# API Documentation

## Session Management

### GET /getSessionDetail
Retrieve session information

**Parameters:**
- `sessionid`: Session identifier

**Response:**
```json
{
  "session_id": "string",
  "user_name": "string",
  "created_at": "timestamp",
  "status": "active|completed"
}
```

## Essay Topic Training

### GET /getEssayTopic
Retrieve essay topic for analysis training

**Parameters:**
- `sessionid`: Session identifier

**Response:**
```json
{
  "topic_md": "markdown content of the essay topic"
}
```

### POST /submitEssayOutline
Submit essay outline as image (processed with OCR + AI analysis)

**Parameters:**
- `sessionid`: Session identifier

**Body:**
- Form data with image file (jpg/png format)

**Processing Flow:**
1. OCR processing to extract text from image
2. AI generation of structured outline using `gen_user_outline.txt` prompt
3. AI evaluation of the outline using `ai_judge_outline.txt` prompt
4. Save all results to session data

**Response:**
```json
{
  "success": true,
  "message": "Outline submitted and processed successfully",
  "ocr_filename": "outline_test_20241128_143022.md",
  "text_content": "用户的原始书写内容...",
  "structured_content": {
    "title": "提纲标题",
    "subject": "作文主旨",
    "parts": [
      {
        "part_title": "部分标题",
        "content": "该部分主要内容",
        "examples": ["例子1", "例子2"],
        "quotes": ["名言1", "名言2"],
        "example_content": "【空】"
      }
    ]
  },
  "ai_judgement": {
    "overall_score": 85,
    "detailed_scores": {
      "structure": 22,
      "theme_relevance": 20,
      "language": 23,
      "creativity": 20
    },
    "strengths": ["优点1", "优点2"],
    "improvements": ["改进建议1", "改进建议2"],
    "comments": "总体评价"
  },
  "judgement_success": true
  "text_content": "OCR extracted text preview..."
}
```

## Testing Endpoints

### POST /test/ai
Test AI processing functionality

**Body:**
```json
{
  "text_content": "用户书写的内容文本"
}
```

**Response:**
```json
{
  "success": true,
  "text_content": "输入的原始文本",
  "structured_content": {
    "title": "AI生成的提纲标题",
    "subject": "作文主旨",
    "parts": [...]
  },
  "ai_judgement": {
    "overall_score": 85,
    "detailed_scores": {...},
    "strengths": [...],
    "improvements": [...],
    "comments": "总体评价"
  }
}
```

**Note:** Images are processed using PaddleOCR API and only the extracted text content is stored.

## Imitation Training

### GET /getImitation
Retrieve imitation materials and previous works

**Parameters:**
- `sessionid`: Session identifier

**Response:**
```json
{
  "imitations": {
    "1": {
      "origin_md": "markdown content of original text",
      "prev_works": ["base64_image1", "base64_image2"]
    },
    "2": {
      "origin_md": "markdown content of original text",
      "prev_works": ["base64_image1"]
    }
  }
}
```

### POST /submitImitation
Submit imitation work as image (processed with OCR)

**Parameters:**
- `sessionid`: Session identifier
- `imitid`: Imitation segment number

**Body:**
- Form data with image file (jpg/png format)

**Response:**
```json
{
  "success": true,
  "message": "Imitation submitted and processed successfully",
  "ocr_filename": "imitation_test_1_20241128_143022.md",
  "imitid": "1",
  "text_content": "OCR extracted text content..."
}
```

**Note:** Images are processed using PaddleOCR API and only the extracted text content is stored.

## OCR Results Access

### GET /getOCRResult
Retrieve OCR processed results

**Parameters:**
- `sessionid`: Session identifier
- `type`: Result type ('essay' or 'imitation')
- `imitid`: Required when type='imitation'

**Response:**
```json
{
  "success": true,
  "result_type": "essay_outline",
  "text_content": "Extracted text from OCR processing",
  "submitted_at": "2024-11-28T14:30:22Z",
  "ocr_filename": "outline_test_20241128_143022.md"
}
```

### GET /ocr/<filename>
Direct access to OCR result files (Markdown format)