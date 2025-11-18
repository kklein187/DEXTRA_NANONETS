#!/usr/bin/env python3
"""Helper script to prepare models for S3 upload.

This script downloads the docling models from Hugging Face and packages them
as tar.gz files ready for upload to Nanonets S3.

Usage:
    python scripts/prepare_s3_models.py
    
Then upload to S3:
    aws s3 cp dist/layout-model-v2.2.0.tar.gz s3://public-vlms/docstrange/
    aws s3 cp dist/tableformer-model-v2.2.0.tar.gz s3://public-vlms/docstrange/
"""

import os
import tarfile
import tempfile
from pathlib import Path
import shutil
import sys

def download_and_package_models():
    """Download models from HF and package for S3."""
    
    # Ensure we have huggingface_hub
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("Please install huggingface_hub: pip install huggingface_hub")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path("dist")
    output_dir.mkdir(exist_ok=True)
    
    # Download the entire repo first
    repo_id = "ds4sd/docling-models"
    revision = "v2.2.0"
    
    print(f"⬇️  Downloading entire repository {repo_id}...")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        repo_path = tmp_path / "repo"
        
        try:
            download_path = snapshot_download(
                repo_id=repo_id,
                revision=revision,
                local_dir=str(repo_path)
            )
            print(f"✅ Downloaded to {download_path}")
        except Exception as e:
            print(f"❌ Failed to download {repo_id}: {e}")
            return
        
        # Check contents
        if not repo_path.exists():
            print(f"❌ Download path {repo_path} does not exist")
            return
            
        artifacts_path = repo_path / "model_artifacts"
        if not artifacts_path.exists():
            print(f"❌ model_artifacts directory not found")
            return
            
        print(f"📁 Found model_artifacts directory")
        
        # Define models to package (EasyOCR downloads its own models)
        models = [
            {
                "name": "layout-model-v2.2.0",
                "source_path": artifacts_path / "layout",
            },
            {
                "name": "tableformer-model-v2.2.0", 
                "source_path": artifacts_path / "tableformer",
            }
        ]
        
        # Package each model
        for model in models:
            print(f"\n📦 Processing {model['name']}...")
            
            output_file = output_dir / f"{model['name']}.tar.gz"
            source_path = model['source_path']
            
            if not source_path.exists():
                print(f"⚠️  {source_path} does not exist, skipping...")
                continue
                
            if output_file.exists():
                print(f"✅ {output_file} already exists, skipping...")
                continue
            
            # List contents for debugging
            contents = list(source_path.rglob("*"))
            print(f"📁 Found {len(contents)} items in {source_path}")
            if contents:
                print(f"📄 Sample files: {[str(p.relative_to(source_path)) for p in contents[:5] if p.is_file()]}")
            
            # Create tar.gz archive
            print(f"📦 Creating archive {output_file}...")
            with tarfile.open(output_file, 'w:gz') as tar:
                # Add all contents from source_path
                for item in source_path.rglob("*"):
                    if item.is_file():
                        arcname = str(item.relative_to(source_path))
                        tar.add(item, arcname=arcname)
            
            print(f"✅ Created {output_file} ({output_file.stat().st_size / 1024 / 1024:.1f} MB)")
    
    print(f"\n🎉 All models packaged in {output_dir}/")
    print("\n📤 To upload to S3, run:")
    print("aws s3 cp dist/layout-model-v2.2.0.tar.gz s3://public-vlms/docstrange/ --acl public-read")
    print("aws s3 cp dist/tableformer-model-v2.2.0.tar.gz s3://public-vlms/docstrange/ --acl public-read")
    
    print("\n🔧 EasyOCR downloads its own models automatically, no S3 upload needed!")

if __name__ == "__main__":
    download_and_package_models() 