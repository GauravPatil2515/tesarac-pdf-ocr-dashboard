"""
Enhanced PDF to Text Processing Module
Professional grade with comprehensive error handling and logging
"""

import os
import sys
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import fitz  # PyMuPDF
from pathlib import Path
import re
import subprocess
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PDFProcessorError(Exception):
    """Custom exception for PDF processing errors"""
    pass


class SystemDependencyError(Exception):
    """Custom exception for missing system dependencies"""
    pass


class PDFProcessor:
    """Professional PDF Processing class with comprehensive error handling"""
    
    def __init__(self):
        """Initialize the PDF processor with dependency checks"""
        try:
            self._setup_paths()
            self.tesseract_available = self._check_tesseract()
            self.poppler_available = self._check_poppler()
            
            if not self.tesseract_available:
                logger.warning("Tesseract OCR not available - OCR functionality will be limited")
            if not self.poppler_available:
                logger.warning("Poppler not available - PDF to image conversion may fail")
                
            logger.info("PDFProcessor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PDFProcessor: {e}")
            raise SystemDependencyError(f"System initialization failed: {e}")
    
    def _setup_paths(self) -> None:
        """Setup system paths for Tesseract and Poppler"""
        try:
            # Add Tesseract to PATH
            tesseract_paths = [
                r"C:\Program Files\Tesseract-OCR",
                r"C:\Program Files (x86)\Tesseract-OCR"
            ]
            
            for tesseract_path in tesseract_paths:
                if os.path.exists(tesseract_path):
                    current_path = os.environ.get('PATH', '')
                    if tesseract_path not in current_path:
                        os.environ['PATH'] = f"{current_path};{tesseract_path}"
                    
                    # Set Tesseract executable path
                    tesseract_exe = os.path.join(tesseract_path, "tesseract.exe")
                    if os.path.exists(tesseract_exe):
                        pytesseract.pytesseract.tesseract_cmd = tesseract_exe
                    break
            
            # Add Poppler to PATH
            username = os.getenv('USERNAME', '')
            poppler_paths = [
                rf"C:\Users\{username}\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-24.08.0\Library\bin",
                r"C:\Program Files\poppler\bin",
                r"C:\poppler\bin"
            ]
            
            for poppler_path in poppler_paths:
                if os.path.exists(poppler_path):
                    current_path = os.environ.get('PATH', '')
                    if poppler_path not in current_path:
                        os.environ['PATH'] = f"{current_path};{poppler_path}"
                    break
                    
        except Exception as e:
            logger.error(f"Error setting up system paths: {e}")
            raise
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available and working"""
        try:
            result = subprocess.run(
                ['tesseract', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                logger.info(f"Tesseract available: {version}")
                return True
            else:
                logger.warning(f"Tesseract check failed with return code: {result.returncode}")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.warning(f"Tesseract not found: {e}")
            return False
    
    def _check_poppler(self) -> bool:
        """Check if Poppler is available and working"""
        try:
            result = subprocess.run(
                ['pdftoppm', '-h'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                logger.info("Poppler available and working")
                return True
            else:
                logger.warning(f"Poppler check failed with return code: {result.returncode}")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.warning(f"Poppler not found: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'tesseract': self.tesseract_available,
            'poppler': self.poppler_available,
            'ready': self.tesseract_available and self.poppler_available,
            'python_version': sys.version,
            'timestamp': datetime.now().isoformat()
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and format extracted text with comprehensive processing"""
        if not text or not text.strip():
            return ""
        
        try:
            # Remove excessive whitespace
            text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
            text = re.sub(r'[ \t]+', ' ', text)
            text = re.sub(r'[ \t]*\n[ \t]*', '\n', text)
            
            # Fix common OCR errors
            text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
            text = re.sub(r'(\w)([.!?])(\w)', r'\1\2 \3', text)
            
            # Clean up lines
            lines = text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if line:
                    # Capitalize first letter after periods
                    line = re.sub(r'(^|\. )([a-z])', lambda m: m.group(1) + m.group(2).upper(), line)
                    cleaned_lines.append(line)
                elif cleaned_lines and cleaned_lines[-1]:
                    cleaned_lines.append('')
            
            result = '\n'.join(cleaned_lines)
            logger.debug(f"Text cleaned: {len(text)} -> {len(result)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Error cleaning text: {e}")
            return text  # Return original text if cleaning fails
    
    def _extract_text_pymupdf(self, pdf_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract text using PyMuPDF with comprehensive error handling"""
        try:
            logger.info(f"Starting PyMuPDF extraction for: {pdf_path.name}")
            doc = fitz.open(str(pdf_path))
            full_text = ""
            page_count = len(doc)
            
            for page_num in range(page_count):
                try:
                    page = doc.load_page(page_num)
                    page_text = page.get_text()
                    
                    if page_text.strip():
                        full_text += f"\n--- PAGE {page_num + 1} ---\n"
                        full_text += page_text + "\n"
                    
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num + 1}: {e}")
                    continue
            
            doc.close()
            
            metadata = {
                'method': 'PyMuPDF',
                'pages_processed': page_count,
                'success': True,
                'char_count': len(full_text)
            }
            
            logger.info(f"PyMuPDF extraction completed: {len(full_text)} characters from {page_count} pages")
            return self._clean_text(full_text), metadata
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            raise PDFProcessorError(f"PyMuPDF extraction failed: {e}")
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy with error handling"""
        try:
            # Convert PIL to OpenCV format
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding
            processed = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            return Image.fromarray(processed)
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original: {e}")
            return image
    
    def _extract_text_ocr(self, pdf_path: Path, dpi: int = 300) -> Tuple[str, Dict[str, Any]]:
        """Extract text using OCR with comprehensive error handling"""
        if not self.poppler_available:
            raise PDFProcessorError("Poppler not available for PDF to image conversion")
        
        if not self.tesseract_available:
            raise PDFProcessorError("Tesseract not available for OCR")
        
        try:
            logger.info(f"Starting OCR extraction for: {pdf_path.name} at {dpi} DPI")
            
            # Convert PDF to images
            images = convert_from_path(str(pdf_path), dpi=dpi, fmt='png')
            full_text = ""
            pages_processed = 0
            
            for page_num, image in enumerate(images, 1):
                try:
                    logger.debug(f"Processing page {page_num}/{len(images)}")
                    
                    # Preprocess image
                    processed_image = self._preprocess_image(image)
                    
                    # Extract text using Tesseract
                    page_text = pytesseract.image_to_string(
                        processed_image, 
                        config='--oem 3 --psm 6'
                    )
                    
                    if page_text.strip():
                        full_text += f"\n--- PAGE {page_num} ---\n"
                        full_text += page_text + "\n"
                    
                    pages_processed += 1
                    
                except Exception as e:
                    logger.warning(f"Error processing page {page_num}: {e}")
                    continue
            
            metadata = {
                'method': 'OCR',
                'pages_processed': pages_processed,
                'total_pages': len(images),
                'dpi': dpi,
                'success': True,
                'char_count': len(full_text)
            }
            
            logger.info(f"OCR extraction completed: {len(full_text)} characters from {pages_processed}/{len(images)} pages")
            return self._clean_text(full_text), metadata
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise PDFProcessorError(f"OCR extraction failed: {e}")
    
    def process_file(self, pdf_path: Path, use_ocr: bool = False, fallback_to_ocr: bool = True) -> Dict[str, Any]:
        """
        Process a PDF file with comprehensive error handling and fallback options
        
        Args:
            pdf_path: Path to the PDF file
            use_ocr: Force OCR extraction
            fallback_to_ocr: Fallback to OCR if direct extraction fails
            
        Returns:
            Dictionary with processing results and metadata
        """
        try:
            # Validate input
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            if not pdf_path.suffix.lower() == '.pdf':
                raise ValueError(f"File is not a PDF: {pdf_path}")
            
            logger.info(f"Processing PDF: {pdf_path.name}")
            start_time = datetime.now()
            
            extracted_text = ""
            metadata = {}
            
            if use_ocr:
                # Force OCR extraction
                try:
                    extracted_text, metadata = self._extract_text_ocr(pdf_path)
                except PDFProcessorError as e:
                    return {
                        'success': False,
                        'error': str(e),
                        'file': str(pdf_path),
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                # Try direct extraction first
                try:
                    extracted_text, metadata = self._extract_text_pymupdf(pdf_path)
                    
                    # Check if extraction was successful
                    if not extracted_text.strip():
                        if fallback_to_ocr:
                            logger.info("Direct extraction yielded no text, falling back to OCR")
                            extracted_text, metadata = self._extract_text_ocr(pdf_path)
                        else:
                            raise PDFProcessorError("No text extracted and OCR fallback disabled")
                            
                except PDFProcessorError as e:
                    if fallback_to_ocr:
                        logger.info(f"Direct extraction failed, falling back to OCR: {e}")
                        try:
                            extracted_text, metadata = self._extract_text_ocr(pdf_path)
                        except PDFProcessorError as ocr_error:
                            return {
                                'success': False,
                                'error': f"Both direct extraction and OCR failed. Direct: {e}, OCR: {ocr_error}",
                                'file': str(pdf_path),
                                'timestamp': datetime.now().isoformat()
                            }
                    else:
                        return {
                            'success': False,
                            'error': str(e),
                            'file': str(pdf_path),
                            'timestamp': datetime.now().isoformat()
                        }
            
            # Validate extracted text
            if not extracted_text or not extracted_text.strip():
                return {
                    'success': False,
                    'error': "No text could be extracted from the PDF",
                    'file': str(pdf_path),
                    'timestamp': datetime.now().isoformat()
                }
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'success': True,
                'text': extracted_text,
                'file': str(pdf_path),
                'filename': pdf_path.name,
                'char_count': len(extracted_text),
                'word_count': len(extracted_text.split()),
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                **metadata
            }
            
            logger.info(f"Successfully processed {pdf_path.name}: {result['char_count']} characters in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error processing {pdf_path}: {e}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': f"Unexpected error: {e}",
                'file': str(pdf_path),
                'timestamp': datetime.now().isoformat()
            }
    
    def process_multiple_files(self, pdf_files: List[Path], use_ocr: bool = False) -> List[Dict[str, Any]]:
        """Process multiple PDF files with comprehensive error handling"""
        results = []
        
        logger.info(f"Starting batch processing of {len(pdf_files)} files")
        
        for i, pdf_file in enumerate(pdf_files, 1):
            try:
                logger.info(f"Processing file {i}/{len(pdf_files)}: {pdf_file.name}")
                result = self.process_file(pdf_file, use_ocr=use_ocr)
                result['batch_index'] = i
                result['batch_total'] = len(pdf_files)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'file': str(pdf_file),
                    'filename': pdf_file.name,
                    'batch_index': i,
                    'batch_total': len(pdf_files),
                    'timestamp': datetime.now().isoformat()
                })
        
        successful = sum(1 for r in results if r['success'])
        logger.info(f"Batch processing completed: {successful}/{len(pdf_files)} files successful")
        
        return results


def create_processor() -> PDFProcessor:
    """Factory function to create a PDFProcessor instance with error handling"""
    try:
        return PDFProcessor()
    except Exception as e:
        logger.error(f"Failed to create PDFProcessor: {e}")
        raise SystemDependencyError(f"Cannot create PDF processor: {e}")


# Export main classes and functions
__all__ = ['PDFProcessor', 'PDFProcessorError', 'SystemDependencyError', 'create_processor']
