# S3 Model Hosting Setup

This directory contains scripts for managing model hosting on Nanonets S3.

## Model Hosting Infrastructure

The docstrange uses a dual hosting system:
1. **Primary**: Nanonets S3 bucket (`public-vlms`) - faster, no authentication required
2. **Fallback**: Hugging Face Hub - original source, requires authentication for some models

## Files

- `prepare_s3_models.py` - Downloads models from Hugging Face and packages them for S3 upload

## Current S3 Setup

**Bucket**: `public-vlms`
**Region**: `us-west-2`
**Base URL**: `https://public-vlms.s3-us-west-2.amazonaws.com/docstrange/`

### Hosted Models

1. **Layout Model** (`layout-model-v2.2.0.tar.gz`) - 151.8 MB
   - Source: `ds4sd/docling-models` model_artifacts/layout
   - Used for: Document layout detection and segmentation

2. **TableFormer Model** (`tableformer-model-v2.2.0.tar.gz`) - 317.5 MB  
   - Source: `ds4sd/docling-models` model_artifacts/tableformer
   - Used for: Table structure recognition and extraction

3. **EasyOCR** - Handled automatically by the EasyOCR library
   - No S3 hosting needed - downloads its own models

## Usage

### One-time Setup (Already Completed)

1. Run the preparation script:
```bash
python scripts/prepare_s3_models.py
```

2. Upload to S3:
```bash
aws s3 cp dist/layout-model-v2.2.0.tar.gz s3://public-vlms/docstrange/ --acl public-read
aws s3 cp dist/tableformer-model-v2.2.0.tar.gz s3://public-vlms/docstrange/ --acl public-read
```

### Model Download Behavior

The `ModelDownloader` class automatically:
1. Tries S3 first (faster, no auth required)
2. Falls back to Hugging Face if S3 fails
3. Provides graceful degradation if no models available

## Environment Variables

- `document_extractor_PREFER_HF=true` - Force use of Hugging Face instead of S3

## Benefits of S3 Hosting

- ✅ **No Authentication Required** - Works out of the box
- ✅ **Faster Downloads** - Optimized S3 delivery
- ✅ **High Availability** - Redundant storage
- ✅ **Cost Effective** - Public bucket with efficient delivery
- ✅ **Fallback Support** - Automatic Hugging Face fallback 