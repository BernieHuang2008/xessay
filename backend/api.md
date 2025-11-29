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
Submit essay outline as image (processed with OCR)

**Parameters:**
- `sessionid`: Session identifier

**Body:**
- Form data with image file (jpg/png format)

**Response:**
```json
{
  "success": true,
  "message": "Outline submitted and processed successfully",
  "ocr_filename": "outline_test_20241128_143022.md",
  "text_content": "OCR extracted text content..."
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