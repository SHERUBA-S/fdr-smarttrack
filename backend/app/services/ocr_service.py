import re
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
from PIL import Image, ImageEnhance, ImageFilter
from pypdf import PdfReader
from app.core.config import settings

logger = logging.getLogger(__name__)

# Try importing pytesseract
try:
    import pytesseract
    # Configure custom tesseract path if provided
    if settings.TESSERACT_CMD and os.path.exists(settings.TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    elif os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    PYTESSERACT_AVAILABLE = True
except Exception:
    PYTESSERACT_AVAILABLE = False

class OCRService:
    @staticmethod
    def is_ocr_engine_available() -> bool:
        """Check if pytesseract and the underlying binary are executable."""
        if not PYTESSERACT_AVAILABLE:
            return False
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    @staticmethod
    def preprocess_image(image_path: str) -> Image.Image:
        """Enhance image for optical character recognition."""
        img = Image.open(image_path)
        # Convert to grayscale
        gray = img.convert("L")
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(1.8)
        # Slight sharpening
        sharpened = enhanced.filter(ImageFilter.SHARPEN)
        return sharpened

    @classmethod
    def extract_text_from_file(cls, file_path: str) -> Tuple[str, bool, Optional[str]]:
        """
        Extract raw text from PDF or image.
        Returns:
            (extracted_text, success, error_message)
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".pdf":
            try:
                reader = PdfReader(file_path)
                text_parts = []
                for idx, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_parts.append(page_text)
                
                full_text = "\n".join(text_parts)
                if full_text.strip():
                    return full_text, True, None
                
                # If PDF has no embedded text (scanned PDF)
                if not cls.is_ocr_engine_available():
                    return "", False, "PDF contains scanned images without embedded text, and OCR engine (Tesseract) is not installed."
                
                return "", False, "Scanned PDF OCR requires image rasterization tool."
            except Exception as e:
                logger.error(f"PDF extraction error: {e}")
                return "", False, f"Failed to extract text from PDF: {str(e)}"
                
        elif ext in [".png", ".jpg", ".jpeg"]:
            if not cls.is_ocr_engine_available():
                return "", False, "OCR engine (Tesseract) is unavailable on this host."
            try:
                processed_img = cls.preprocess_image(file_path)
                ocr_text = pytesseract.image_to_string(processed_img)
                return ocr_text, True, None
            except Exception as e:
                logger.error(f"Image OCR error: {e}")
                return "", False, f"OCR processing failed: {str(e)}"
                
        return "", False, f"Unsupported file extension: {ext}"

    @classmethod
    def parse_fdr_fields(cls, raw_text: str) -> List[Dict[str, Any]]:
        """
        Parse structured fields from raw OCR text using regex heuristics with confidence scoring.
        Returns a list of field dictionaries for ExtractedDocumentField.
        """
        fields = []
        if not raw_text:
            return fields

        # 1. FDR Reference Number
        fdr_match = re.search(
            r"(?:FDR|Fixed\s*Deposit|Receipt|FDR\s*No\.?|A/C\s*No\.?|Ref\s*No\.?)[:\s#\-\.]*([A-Z0-9\/\-]{6,25})",
            raw_text,
            re.IGNORECASE
        )
        if fdr_match:
            val = fdr_match.group(1).strip()
            fields.append({
                "field_name": "fdr_number",
                "extracted_value": val,
                "confidence": 0.88 if len(val) >= 8 else 0.72,
                "page_number": 1
            })

        # 2. Principal Amount (e.g. Rs. 5,00,000.00 or INR 500000 or ₹ 5,00,000)
        amount_match = re.search(
            r"(?:Rs\.?|INR|₹|Principal\s*Amount|Amount|Deposit\s*Amount)[:\s]*([0-9,]+(?:\.[0-9]{2})?)",
            raw_text,
            re.IGNORECASE
        )
        if amount_match:
            raw_amt = amount_match.group(1).replace(",", "").strip()
            try:
                amt_dec = Decimal(raw_amt)
                fields.append({
                    "field_name": "principal_amount",
                    "extracted_value": str(amt_dec),
                    "confidence": 0.85,
                    "page_number": 1
                })
            except Exception:
                pass

        # 3. Dates (Issue date and Maturity date)
        # Matches DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD
        date_pattern = r"(\b\d{1,2}[-\/]\d{1,2}[-\/]\d{4}\b|\b\d{4}[-\/]\d{1,2}[-\/]\d{1,2}\b)"
        
        issue_match = re.search(
            rf"(?:Issue\s*Date|Date\s*of\s*Issue|Opened\s*Date|Deposit\s*Date)[:\s]*{date_pattern}",
            raw_text,
            re.IGNORECASE
        )
        if issue_match:
            fields.append({
                "field_name": "issue_date",
                "extracted_value": issue_match.group(1).strip(),
                "confidence": 0.82,
                "page_number": 1
            })

        maturity_match = re.search(
            rf"(?:Maturity\s*Date|Due\s*Date|Date\s*of\s*Maturity)[:\s]*{date_pattern}",
            raw_text,
            re.IGNORECASE
        )
        if maturity_match:
            fields.append({
                "field_name": "maturity_date",
                "extracted_value": maturity_match.group(1).strip(),
                "confidence": 0.85,
                "page_number": 1
            })

        # 4. Interest Rate (e.g. 7.25% or Interest Rate: 6.50)
        rate_match = re.search(
            r"(?:Interest\s*Rate|ROI|Rate\s*of\s*Interest)[:\s]*([0-9]+(?:\.[0-9]{1,2})?)\s*%",
            raw_text,
            re.IGNORECASE
        )
        if rate_match:
            fields.append({
                "field_name": "interest_rate",
                "extracted_value": rate_match.group(1).strip(),
                "confidence": 0.80,
                "page_number": 1
            })

        # 5. Bank Name Heuristic
        known_banks = [
            "State Bank of India", "SBI", "Punjab National Bank", "PNB",
            "HDFC Bank", "ICICI Bank", "Bank of Baroda", "Canara Bank",
            "Union Bank of India", "Axis Bank", "Indian Bank", "Kotak Mahindra Bank"
        ]
        for b in known_banks:
            if re.search(rf"\b{re.escape(b)}\b", raw_text, re.IGNORECASE):
                fields.append({
                    "field_name": "bank_name",
                    "extracted_value": b,
                    "confidence": 0.90,
                    "page_number": 1
                })
                break

        # 6. Institution Name / Account Holder
        inst_match = re.search(
            r"(?:In\s*Favor\s*of|Favoring|Account\s*Name|Depositor|Institution)[:\s]*([A-Za-z0-9\s,\.\-]{5,60})",
            raw_text,
            re.IGNORECASE
        )
        if inst_match:
            fields.append({
                "field_name": "institution_name",
                "extracted_value": inst_match.group(1).strip(),
                "confidence": 0.75,
                "page_number": 1
            })

        return fields
