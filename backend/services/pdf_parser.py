import io
import logging
from typing import Optional, List
import PyPDF2

logger = logging.getLogger(__name__)

async def extract_pdf_text(pdf_content: bytes, filename: str = "unknown") -> str:
    """
    Extract text from PDF with multiple fallback methods
    """
    methods = [
        _extract_with_pypdf2,
        _extract_with_pypdf2_fallback,
        _extract_simple_text
    ]
    
    for i, method in enumerate(methods):
        try:
            logger.info(f"Trying PDF extraction method {i+1} for {filename}")
            text = method(pdf_content)
            
            if text and len(text.strip()) > 50:  # Require minimum text length
                logger.info(f"Successfully extracted {len(text)} characters using method {i+1}")
                return clean_extracted_text(text)
            else:
                logger.warning(f"Method {i+1} extracted insufficient text ({len(text) if text else 0} chars)")
                
        except Exception as e:
            logger.warning(f"PDF extraction method {i+1} failed for {filename}: {e}")
            continue
    
    # If all methods fail, return a helpful error message
    logger.error(f"All PDF extraction methods failed for {filename}")
    return f"[Error: Could not extract text from PDF '{filename}'. The file may be image-based, encrypted, or corrupted.]"

def _extract_with_pypdf2(pdf_content: bytes) -> str:
    """Primary extraction method using PyPDF2"""
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    
    # Check if PDF is encrypted
    if pdf_reader.is_encrypted:
        # Try to decrypt with empty password (common case)
        if not pdf_reader.decrypt(""):
            raise ValueError("PDF is password protected")
    
    text_parts = []
    for page_num, page in enumerate(pdf_reader.pages):
        try:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        except Exception as e:
            logger.warning(f"Failed to extract page {page_num}: {e}")
            continue
    
    return "\n".join(text_parts)

def _extract_with_pypdf2_fallback(pdf_content: bytes) -> str:
    """Fallback method with different PyPDF2 settings"""
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    
    text_parts = []
    for page_num, page in enumerate(pdf_reader.pages):
        try:
            # Try different extraction approaches
            if hasattr(page, 'extractText'):  # Older PyPDF2 versions
                page_text = page.extractText()
            else:
                page_text = page.extract_text()
            
            if page_text:
                text_parts.append(page_text)
                
        except Exception as e:
            logger.warning(f"Fallback extraction failed for page {page_num}: {e}")
            # Try to get raw content objects
            try:
                if '/Contents' in page:
                    content = str(page['/Contents'])
                    # Extract visible text patterns
                    import re
                    text_matches = re.findall(r'\\((.*?)\\)', content)
                    if text_matches:
                        text_parts.append(' '.join(text_matches))
            except:
                pass
            continue
    
    return "\n".join(text_parts)

def _extract_simple_text(pdf_content: bytes) -> str:
    """Simple text extraction for basic PDFs"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        
        # Get basic info
        text_parts = []
        
        # Try to extract metadata as fallback
        if pdf_reader.metadata:
            if '/Title' in pdf_reader.metadata:
                text_parts.append(f"Title: {pdf_reader.metadata['/Title']}")
            if '/Author' in pdf_reader.metadata:
                text_parts.append(f"Author: {pdf_reader.metadata['/Author']}")
            if '/Subject' in pdf_reader.metadata:
                text_parts.append(f"Subject: {pdf_reader.metadata['/Subject']}")
        
        # Try simple page iteration
        for page in pdf_reader.pages[:3]:  # Only first 3 pages for safety
            try:
                text = str(page.extract_text())
                if text and len(text) > 10:
                    text_parts.append(text)
            except:
                pass
                
        return "\n".join(text_parts)
        
    except Exception as e:
        logger.error(f"Simple extraction failed: {e}")
        return ""

def clean_extracted_text(text: str) -> str:
    """Clean and normalize extracted text"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    import re
    
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove common PDF artifacts
    text = re.sub(r'\\x[0-9a-fA-F]{2}', '', text)  # Remove hex codes
    text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)  # Keep only printable ASCII + newlines
    
    # Remove page numbers (common patterns)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)  # Standalone numbers
    text = re.sub(r'\nPage \d+\n', '\n', text)   # "Page X" patterns
    
    # Clean up spacing
    text = text.strip()
    
    return text

def validate_pdf_content(pdf_content: bytes) -> tuple[bool, str]:
    """Validate PDF file before processing"""
    if len(pdf_content) < 100:
        return False, "File is too small to be a valid PDF"
    
    # Check PDF signature
    if not pdf_content.startswith(b'%PDF-'):
        return False, "File is not a valid PDF (missing PDF signature)"
    
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        
        # Check if PDF has pages
        if len(pdf_reader.pages) == 0:
            return False, "PDF contains no pages"
        
        # Check if PDF is too large (too many pages)
        if len(pdf_reader.pages) > 50:
            return False, "PDF has too many pages (maximum 50 pages)"
        
        return True, "PDF is valid"
        
    except Exception as e:
        return False, f"PDF validation failed: {str(e)}"