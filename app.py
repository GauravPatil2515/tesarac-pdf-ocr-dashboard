"""
Flask API Backend for PDF Processing Dashboard
RESTful API with comprehensive error handling and logging
"""

from flask import Flask, request, jsonify, send_file, send_from_directory, render_template
from flask_cors import CORS
import os
import sys
from pathlib import Path
import tempfile
import zipfile
import io
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import traceback
from collections import defaultdict
from time import time
import gzip

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))
from pdf_processor import PDFProcessor, PDFProcessorError, SystemDependencyError

# Configure optimized logging
logging.basicConfig(
    level=logging.WARNING,  # Reduced logging for production
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log', delay=True),  # Lazy file creation
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app with optimizations
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Performance optimizations
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache for static files
app.config['TEMPLATES_AUTO_RELOAD'] = False  # Disable template auto-reload in production
app.config['JSON_SORT_KEYS'] = False  # Faster JSON serialization

CORS(app, 
     origins=['http://localhost:5000', 'http://127.0.0.1:5000'],  # Restrict to specific origins
     methods=['GET', 'POST'],  # Only allow necessary methods
     allow_headers=['Content-Type'],  # Restrict headers
     max_age=3600)  # Cache preflight requests for 1 hour

# Configuration with security considerations
app.config.update(
    MAX_CONTENT_LENGTH=100 * 1024 * 1024,  # 100MB max file size
    UPLOAD_FOLDER='uploads',
    OUTPUT_FOLDER='outputs',
    ALLOWED_EXTENSIONS={'pdf'},
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
)

# Global processor instance (lazy-loaded for performance)
processor = None

def get_processor():
    """Get processor instance with lazy initialization"""
    global processor
    if processor is None:
        try:
            processor = PDFProcessor()
            logger.info("PDF Processor initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PDF processor: {e}")
            raise
    return processor

def secure_save_file(file, upload_folder):
    """Efficiently save uploaded file with enhanced security checks"""
    filename = secure_filename(file.filename)
    if not filename:
        raise ValueError("Invalid filename")
    
    # Generate secure filename to prevent attacks
    filename = generate_secure_filename(file.filename)
    file_path = Path(upload_folder) / filename
    
    # Stream save for large files
    try:
        file.save(str(file_path))
        
        # Validate file content after saving
        if not validate_pdf_content(file_path):
            file_path.unlink()  # Remove invalid file
            raise ValueError("Invalid PDF file content")
            
        return str(file_path)
    except Exception as e:
        if file_path.exists():
            file_path.unlink()  # Cleanup on failure
        raise e

def allowed_file(filename):
    """Check if file extension is allowed with proper validation"""
    if not filename or '.' not in filename:
        return False
    
    try:
        extension = Path(filename).suffix.lower().lstrip('.')
        return extension in app.config['ALLOWED_EXTENSIONS']
    except Exception as e:
        logger.error(f"Error checking file extension for {filename}: {e}")
        return False

def handle_error(error_msg, status_code=500, details=None):
    """Centralized error handling"""
    logger.error(f"API Error: {error_msg}")
    if details:
        logger.error(f"Error details: {details}")
    
    response = {
        'success': False,
        'error': error_msg,
        'timestamp': datetime.now().isoformat()
    }
    
    if details and app.debug:
        response['details'] = str(details)
    
    return jsonify(response), status_code

def ensure_directories():
    """Ensure upload and output directories exist"""
    try:
        Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
        Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        return False

# Initialize directories on startup
with app.app_context():
    ensure_directories()

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    """Handle file size limit exceeded"""
    return handle_error("File too large. Maximum size is 100MB.", 413)

@app.errorhandler(413)
def handle_payload_too_large(e):
    """Handle payload too large"""
    return handle_error("Request payload too large.", 413)

@app.errorhandler(429)
def handle_rate_limit_exceeded(e):
    """Handle rate limit exceeded"""
    return handle_error("Rate limit exceeded. Please wait before making more requests.", 429)

@app.errorhandler(500)
def handle_internal_error(e):
    """Handle internal server errors"""
    return handle_error("Internal server error occurred.", 500, str(e))

# Rate limiting configuration
request_counts = defaultdict(list)

def rate_limit_check(key, limit=10, window=60):
    """Simple rate limiting: limit requests per window (seconds)"""
    now = time()
    # Clean old requests
    request_counts[key] = [req_time for req_time in request_counts[key] if now - req_time < window]
    
    if len(request_counts[key]) >= limit:
        return False
    
    request_counts[key].append(now)
    return True

def get_client_id():
    """Get client identifier for rate limiting"""
    return request.remote_addr

# Add response compression
def compress_response(response):
    """Compress JSON responses for better performance"""
    if (response.content_type and 
        'application/json' in response.content_type and 
        len(response.data) > 500):  # Only compress larger responses
        
        compressed_data = gzip.compress(response.data)
        if len(compressed_data) < len(response.data):
            response.data = compressed_data
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = len(compressed_data)
    
    return response

@app.after_request
def after_request(response):
    """Add security headers and compression"""
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Compress response if applicable
    if 'gzip' in request.headers.get('Accept-Encoding', ''):
        response = compress_response(response)
    
    return response

# API Routes
@app.route('/')
def index():
    """Serve the main dashboard page with caching"""
    try:
        response = app.make_response(render_template('index.html'))
        # Add caching headers for better performance
        response.headers['Cache-Control'] = 'public, max-age=3600'  # 1 hour cache
        response.headers['ETag'] = 'dashboard-v1'
        return response
    except Exception as e:
        return handle_error("Failed to load dashboard", 500, e)

@app.route('/api/health')
def health_check():
    """Health check endpoint with system status"""
    try:
        proc = get_processor()
        status = proc.get_system_status()
        return jsonify({
            'success': True,
            'status': 'healthy',
            'system_status': status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return handle_error("Health check failed", 500, e)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle single file upload and processing with rate limiting"""
    try:
        # Rate limiting check
        client_id = get_client_id()
        if not rate_limit_check(client_id, limit=10, window=60):  # 10 uploads per minute
            return handle_error("Rate limit exceeded. Please wait before uploading again.", 429)
        
        proc = get_processor()
        
        if 'file' not in request.files:
            return handle_error("No file uploaded", 400)
        
        file = request.files['file']
        if file.filename == '':
            return handle_error("No file selected", 400)
        
        if not allowed_file(file.filename):
            return handle_error("Invalid file type. Only PDF files are allowed.", 400)
        
        # Rate limiting check
        client_id = get_client_id()
        if not rate_limit_check(client_id):
            return handle_error("Too many requests. Please try again later.", 429)
        
        # Get processing options
        use_ocr = request.form.get('use_ocr', 'false').lower() == 'true'
        
        # Save uploaded file efficiently
        file_path = secure_save_file(file, app.config['UPLOAD_FOLDER'])
        logger.info(f"File uploaded: {file.filename}")
        
        # Validate PDF content
        if not validate_pdf_content(file_path):
            return handle_error("Uploaded file is not a valid PDF", 400)
        
        # Process the file
        result = proc.process_file(file_path, use_ocr=use_ocr)
        
        # Save result to output file if successful
        output_filename = None
        if result['success']:
            try:
                # Generate output filename
                base_name = Path(file.filename).stem
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{base_name}_{timestamp}.txt"
                output_path = Path(app.config['OUTPUT_FOLDER']) / output_filename
                
                # Save extracted text
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"PDF Text Extraction Results\n")
                    f.write(f"Source: {file.filename}\n")
                    f.write(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Processing Time: {result.get('processing_time', 0):.2f} seconds\n")
                    f.write(f"Characters: {result.get('char_count', 0)}\n")
                    f.write(f"Words: {result.get('word_count', 0)}\n")
                    f.write("=" * 80 + "\n\n")
                    f.write(result['text'])
                
                # Add output filename to result
                result['output_filename'] = output_filename
                logger.info(f"Saved extraction result to: {output_filename}")
                
            except Exception as save_error:
                logger.error(f"Failed to save result file: {save_error}")
                # Don't fail the whole process if file saving fails
        
        # Clean up uploaded file
        try:
            Path(file_path).unlink()
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup uploaded file: {cleanup_error}")
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'File processed successfully',
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return handle_error(f"Processing failed: {result.get('error', 'Unknown error')}", 422)
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return handle_error("Upload processing failed", 500, e)

@app.route('/api/batch-upload', methods=['POST'])
def batch_upload():
    """Handle multiple file upload and processing with rate limiting"""
    try:
        # Rate limiting check
        client_id = get_client_id()
        if not rate_limit_check(client_id, limit=3, window=60):  # 3 batch uploads per minute
            return handle_error("Rate limit exceeded. Please wait before batch uploading again.", 429)
        
        proc = get_processor()
        
        if 'files' not in request.files:
            return handle_error("No files uploaded", 400)
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return handle_error("No files selected", 400)
        
        # Validate all files
        valid_files = []
        for file in files:
            if file.filename != '' and allowed_file(file.filename):
                valid_files.append(file)
        
        if not valid_files:
            return handle_error("No valid PDF files found", 400)
        
        # Get processing options
        use_ocr = request.form.get('use_ocr', 'false').lower() == 'true'
        
        # Save and process files
        results = []
        file_paths = []
        
        for i, file in enumerate(valid_files):
            try:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_filename = f"{timestamp}_{i}_{filename}"
                file_path = Path(app.config['UPLOAD_FOLDER']) / unique_filename
                
                file.save(str(file_path))
                file_paths.append(file_path)
                
            except Exception as e:
                results.append({
                    'success': False,
                    'error': f"Failed to save file {file.filename}: {e}",
                    'filename': file.filename
                })
        
        # Process all files
        if file_paths:
            batch_results = proc.process_multiple_files(file_paths, use_ocr=use_ocr)
            
            # Save results to output files
            for i, result in enumerate(batch_results):
                if result.get('success', False):
                    try:
                        # Generate output filename
                        original_file = valid_files[i]
                        base_name = Path(original_file.filename).stem
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_filename = f"{base_name}_{timestamp}.txt"
                        output_path = Path(app.config['OUTPUT_FOLDER']) / output_filename
                        
                        # Save extracted text
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(f"PDF Text Extraction Results\n")
                            f.write(f"Source: {original_file.filename}\n")
                            f.write(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write(f"Processing Time: {result.get('processing_time', 0):.2f} seconds\n")
                            f.write(f"Characters: {result.get('char_count', 0)}\n")
                            f.write(f"Words: {result.get('word_count', 0)}\n")
                            f.write("=" * 80 + "\n\n")
                            f.write(result['text'])
                        
                        # Add output filename to result
                        result['output_filename'] = output_filename
                        logger.info(f"Saved extraction result to: {output_filename}")
                        
                    except Exception as save_error:
                        logger.error(f"Failed to save result file: {save_error}")
                        # Don't fail the whole process if file saving fails
            
            results.extend(batch_results)
        
        # Clean up uploaded files
        for file_path in file_paths:
            try:
                file_path.unlink()
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup uploaded file: {cleanup_error}")
        
        successful = sum(1 for r in results if r.get('success', False))
        
        return jsonify({
            'success': True,
            'message': f'Batch processing completed. {successful}/{len(results)} files successful.',
            'results': results,
            'summary': {
                'total': len(results),
                'successful': successful,
                'failed': len(results) - successful
            },
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Batch upload error: {e}")
        logger.error(traceback.format_exc())
        return handle_error("Batch upload processing failed", 500, e)

@app.route('/api/files')
def list_files():
    """List processed files in output directory"""
    try:
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        if not output_dir.exists():
            return jsonify({
                'success': True,
                'files': [],
                'message': 'No files processed yet'
            })
        
        files = []
        for file_path in output_dir.glob('*.txt'):
            try:
                stat = file_path.stat()
                files.append({
                    'filename': file_path.name,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'path': str(file_path.relative_to(output_dir))
                })
            except Exception as e:
                logger.warning(f"Failed to get file info for {file_path}: {e}")
        
        return jsonify({
            'success': True,
            'files': sorted(files, key=lambda x: x['modified'], reverse=True),
            'count': len(files)
        })
    
    except Exception as e:
        return handle_error("Failed to list files", 500, e)

@app.route('/api/download/<filename>')
def download_file(filename):
    """Download a specific processed file"""
    try:
        # Secure filename validation
        safe_filename = secure_filename(filename)
        if not safe_filename.endswith('.txt'):
            return handle_error("Invalid file type", 400)
        
        file_path = Path(app.config['OUTPUT_FOLDER']) / safe_filename
        if not file_path.exists():
            return handle_error("File not found", 404)
        
        return send_file(str(file_path), as_attachment=True, download_name=safe_filename)
    
    except Exception as e:
        return handle_error("Download failed", 500, e)

@app.route('/api/download-all')
def download_all():
    """Download all processed files as ZIP"""
    try:
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        txt_files = list(output_dir.glob('*.txt'))
        
        if not txt_files:
            return handle_error("No files available for download", 404)
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in txt_files:
                try:
                    zip_file.write(str(file_path), file_path.name)
                except Exception as e:
                    logger.warning(f"Failed to add {file_path.name} to ZIP: {e}")
        
        zip_buffer.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"pdf_extracts_{timestamp}.zip"
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )
    
    except Exception as e:
        return handle_error("ZIP download failed", 500, e)

def validate_pdf_content(file_path):
    """Validate that uploaded file is actually a PDF by checking magic bytes"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            # Check for PDF magic bytes
            if header.startswith(b'%PDF-'):
                return True
            return False
    except Exception as e:
        logger.error(f"Error validating file content: {e}")
        return False

def generate_secure_filename(original_filename):
    """Generate secure filename to prevent directory traversal"""
    import secrets
    # Generate secure random string
    secure_suffix = secrets.token_hex(8)
    base_name = secure_filename(Path(original_filename).stem)
    # Limit base name length
    base_name = base_name[:50] if len(base_name) > 50 else base_name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{secure_suffix}_{base_name}.pdf"

if __name__ == '__main__':
    try:
        logger.info("Starting Flask application...")
        # Production optimizations
        debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
        app.run(host='0.0.0.0', port=5000, debug=debug_mode, threaded=True)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)
