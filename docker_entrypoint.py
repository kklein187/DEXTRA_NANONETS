"""
Docker-friendly entrypoint for DocStrange web application.
This wrapper allows the app to run in both GPU and cloud modes in Docker.
"""

import os
import sys

def main():
    """Main entrypoint for Docker container."""
    print("🐳 Starting DocStrange in Docker...")
    print("=" * 60)
    
    # Check for API key
    api_key = os.environ.get('NANONETS_API_KEY')
    
    if not api_key:
        print("")
        print("⚠️  WARNING: No NANONETS_API_KEY found!")
        print("")
        print("DocStrange in Docker requires an API key for cloud processing.")
        print("Interactive authentication (docstrange login) does not work in Docker.")
        print("")
        print("📋 To fix this:")
        print("1. Get your API key from: https://app.nanonets.com/#/keys")
        print("2. Add it to your .env file:")
        print("   NANONETS_API_KEY=your_api_key_here")
        print("3. Restart the container:")
        print("   docker-compose restart docstrange-cloud")
        print("")
        print("🆓 Free tier available: Sign up at https://nanonets.com")
        print("")
        print("=" * 60)
        print("⏸️  Container will continue but API calls will fail without a key.")
        print("=" * 60)
    else:
        print("✅ NANONETS_API_KEY configured")
    
    # Import the web app module
    from docstrange.web_app import app, check_gpu_availability, download_models
    
    # Get configuration from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    
    # Check if we should run in GPU mode
    gpu_available = check_gpu_availability()
    
    if gpu_available:
        print("")
        print("✅ GPU detected - will use GPU mode for processing")
        print("🔄 Downloading GPU models (this may take a few minutes on first run)...")
        try:
            download_models()
            print("✅ Models ready")
        except Exception as e:
            print(f"⚠️  Warning: Could not download models: {e}")
            print("Will proceed anyway - models will download on first use")
    else:
        print("")
        print("💻 GPU not available - will use cloud mode for processing")
    
    print("")
    print("🚀 Starting DocStrange web interface...")
    print(f"🌐 Web UI: http://localhost:{port}")
    print(f"� Health: http://localhost:{port}/api/health")
    print(f"ℹ️  System: http://localhost:{port}/api/system-info")
    print("")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Run the Flask app
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
