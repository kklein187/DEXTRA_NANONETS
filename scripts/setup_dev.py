#!/usr/bin/env python3
"""
Development setup script for docstrange.
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def main():
    """Main setup function."""
    print("🚀 Setting up docstrange development environment...\n")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    
    # Install base dependencies
    if not run_command("pip install -e .", "Installing package in development mode"):
        print("❌ Failed to install package")
        sys.exit(1)
    
    # Install development dependencies
    if not run_command("pip install -e .[dev]", "Installing development dependencies"):
        print("⚠️  Failed to install development dependencies (continuing anyway)")
    
    # Run tests
    print("\n🧪 Running tests...")
    if not run_command("python -m pytest tests/ -v", "Running tests"):
        print("⚠️  Some tests failed (this might be expected for first run)")
    
    # Run example
    print("\n📝 Running basic example...")
    if not run_command("python examples/basic_usage.py", "Running basic usage example"):
        print("⚠️  Example failed (this might be expected for first run)")
    
    print("\n🎉 Setup completed!")
    print("\n📚 Next steps:")
    print("1. Check out the examples/ directory for usage examples")
    print("2. Run 'python -m pytest tests/' to run all tests")
    print("3. Run 'python examples/basic_usage.py' to see the library in action")
    print("4. Check the README.md for detailed documentation")


if __name__ == "__main__":
    main() 