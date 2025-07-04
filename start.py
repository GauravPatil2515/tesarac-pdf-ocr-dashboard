"""
Enhanced Startup Script for Medical PDF OCR Dashboard
Checks dependencies and starts the Flask server
"""

import sys
import os
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_packages():
    """Check if required Python packages are installed"""
    package_imports = {
        'flask': 'flask',
        'flask_cors': 'flask_cors',
        'PyMuPDF': 'fitz',
        'pdf2image': 'pdf2image',
        'pytesseract': 'pytesseract',
        'opencv-python': 'cv2',
        'pillow': 'PIL',
        'numpy': 'numpy',
        'pandas': 'pandas'
    }
    
    missing_packages = []
    
    for package, import_name in package_imports.items():
        try:
            __import__(import_name)
            logger.info(f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"✗ {package} is missing")
    
    return missing_packages

def check_system_dependencies():
    """Check if Tesseract and Poppler are available"""
    dependencies = {'tesseract': False, 'poppler': False}
    
    # Check Tesseract
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            dependencies['tesseract'] = True
            logger.info("✓ Tesseract OCR is available")
        else:
            logger.warning("✗ Tesseract OCR not found")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        logger.warning("✗ Tesseract OCR not found")
    
    # Check Poppler
    try:
        result = subprocess.run(['pdftoppm', '-h'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            dependencies['poppler'] = True
            logger.info("✓ Poppler utilities are available")
        else:
            logger.warning("✗ Poppler utilities not found")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        logger.warning("✗ Poppler utilities not found")
    
    return dependencies

def ensure_directories():
    """Ensure required directories exist"""
    directories = ['uploads', 'outputs']
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(exist_ok=True)
            logger.info(f"Created directory: {directory}")
        else:
            logger.info(f"Directory exists: {directory}")

def start_flask_server():
    """Start the Flask development server"""
    try:
        logger.info("Starting Flask server...")
        logger.info("Dashboard will be available at: http://localhost:5000")
        logger.info("Press Ctrl+C to stop the server")
        
        # Import and run the Flask app
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start Flask server: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🏥 Medical PDF OCR Dashboard - Startup")
    print("=" * 50)
    
    # Check Python packages
    logger.info("Checking Python packages...")
    missing_packages = check_python_packages()
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.error("Please install missing packages with: pip install -r requirements.txt")
        return False
    
    # Check system dependencies
    logger.info("Checking system dependencies...")
    dependencies = check_system_dependencies()
    
    if not dependencies['tesseract']:
        logger.warning("Tesseract OCR not found. OCR functionality will be limited.")
        logger.warning("Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
    
    if not dependencies['poppler']:
        logger.warning("Poppler not found. PDF to image conversion may fail.")
        logger.warning("Install Poppler: https://github.com/oschwartz10612/poppler-windows/releases/")
    
    # Ensure directories
    logger.info("Setting up directories...")
    ensure_directories()
    
    # Start Flask server
    logger.info("All checks completed. Starting server...")
    return start_flask_server()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        sys.exit(1)
