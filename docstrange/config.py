# docstrange/config.py

class InternalConfig:
    # Internal feature flags and defaults (not exposed to end users)
    use_markdownify = True
    ocr_provider = 'neural'  # OCR provider to use (neural for docling models)
    
    # PDF processing configuration
    pdf_to_image_enabled = True  # Convert PDF pages to images for OCR
    pdf_image_dpi = 300  # DPI for PDF to image conversion
    pdf_image_scale = 2.0  # Scale factor for better OCR accuracy
    
    # Add other internal config options here as needed
    # e.g. default_ocr_lang = 'en'
    # e.g. enable_layout_aware_ocr = True 