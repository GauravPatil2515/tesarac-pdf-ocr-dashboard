# API Documentation

## Overview

The Medical PDF OCR Dashboard provides a RESTful API for processing PDF files and extracting text content.

## Base URL

```
http://localhost:5000
```

## Authentication

Currently, no authentication is required. For production deployments, consider implementing proper authentication and authorization.

## Content Types

- Request: `multipart/form-data` for file uploads, `application/json` for other requests
- Response: `application/json`

## Endpoints

### Health Check

```http
GET /api/health
```

Returns system status and health information.

**Response:**
```json
{
  "status": "healthy",
  "success": true,
  "system_status": {
    "poppler": true,
    "python_version": "3.12.6",
    "ready": true,
    "tesseract": true,
    "timestamp": "2025-07-05T01:00:00.000000"
  },
  "timestamp": "2025-07-05T01:00:00.000000"
}
```

### Upload Single File

```http
POST /api/upload
```

Upload and process a single PDF file.

**Parameters:**
- `file` (file, required): PDF file to process
- `use_ocr` (boolean, optional): Enable OCR processing (default: false)

**Response:**
```json
{
  "message": "File processed successfully",
  "result": {
    "char_count": 52583,
    "file": "uploads/20250705_013028_example.pdf",
    "filename": "20250705_013028_example.pdf",
    "method": "PyMuPDF",
    "output_filename": "example_20250705_013028.txt",
    "pages_processed": 4,
    "processing_time": 0.246996,
    "success": true,
    "text": "Extracted text content...",
    "timestamp": "2025-07-05T01:30:28.788396",
    "word_count": 7396
  },
  "success": true,
  "timestamp": "2025-07-05T01:30:28.799319"
}
```

### Batch Upload

```http
POST /api/batch-upload
```

Upload and process multiple PDF files.

**Parameters:**
- `files` (files, required): Multiple PDF files to process
- `use_ocr` (boolean, optional): Enable OCR processing (default: false)

**Response:**
```json
{
  "message": "Batch processing completed",
  "results": [
    {
      "filename": "file1.pdf",
      "success": true,
      "output_filename": "file1_20250705_013028.txt",
      "processing_time": 0.5
    },
    {
      "filename": "file2.pdf",
      "success": false,
      "error": "Processing failed"
    }
  ],
  "summary": {
    "total": 2,
    "successful": 1,
    "failed": 1
  },
  "success": true,
  "timestamp": "2025-07-05T01:30:28.799319"
}
```

### List Files

```http
GET /api/files
```

List all processed output files.

**Response:**
```json
{
  "count": 5,
  "files": [
    {
      "filename": "example_20250705_013028.txt",
      "modified": "2025-07-05T01:30:28.788396",
      "path": "example_20250705_013028.txt",
      "size": 53437
    }
  ],
  "success": true
}
```

### Download File

```http
GET /api/download/<filename>
```

Download a specific processed text file.

**Parameters:**
- `filename` (string, required): Name of the file to download

**Response:**
- Content-Type: `text/plain`
- Content-Disposition: `attachment; filename="filename.txt"`

### Download All Files

```http
GET /api/download-all
```

Download all processed files as a ZIP archive.

**Response:**
- Content-Type: `application/zip`
- Content-Disposition: `attachment; filename="pdf_extracts_TIMESTAMP.zip"`

## Error Responses

All endpoints return structured error responses:

```json
{
  "error": "Error description",
  "success": false,
  "timestamp": "2025-07-05T01:00:00.000000",
  "details": "Additional error details if available"
}
```

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters, file type, etc.)
- `404` - Not Found (file not found)
- `413` - Payload Too Large (file size exceeds limit)
- `500` - Internal Server Error

## Rate Limiting

Currently, no rate limiting is implemented. For production use, consider implementing rate limiting based on your requirements.

## File Size Limits

- Maximum file size: 100MB per file
- Supported formats: PDF only
- No limit on number of files in batch upload

## Examples

### cURL Examples

**Health Check:**
```bash
curl -X GET http://localhost:5000/api/health
```

**Upload Single File:**
```bash
curl -X POST \
  -F "file=@document.pdf" \
  -F "use_ocr=false" \
  http://localhost:5000/api/upload
```

**Download File:**
```bash
curl -X GET \
  -o extracted_text.txt \
  http://localhost:5000/api/download/document_20250705_013028.txt
```

### JavaScript Example

```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('use_ocr', 'false');

fetch('/api/upload', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));

// Download file
fetch('/api/download/filename.txt')
.then(response => response.blob())
.then(blob => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'filename.txt';
  a.click();
});
```
