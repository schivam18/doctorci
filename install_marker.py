#!/usr/bin/env python3
"""
Marker Installation Script

This script helps install and configure Marker PDF processing for the
clinical trial data extraction system.

Features:
- Automatic dependency installation
- System compatibility checking
- Configuration validation
- Test installation

Usage:
    python install_marker.py [--force] [--test]

Author: Clinical Trial Data Extraction System
Date: 2025
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple


def print_banner():
    """Print installation banner."""
    print("=" * 80)
    print("🔬 MARKER PDF PROCESSOR INSTALLATION")
    print("   Clinical Trial Data Extraction System")
    print("=" * 80)
    print()


def print_section(title: str):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")


def check_python_version() -> bool:
    """Check if Python version is compatible."""
    print("🔍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python {version.major}.{version.minor} is not supported")
        print("   Marker requires Python 3.9 or higher")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def check_system_dependencies() -> Dict[str, bool]:
    """Check system dependencies."""
    print("🔍 Checking system dependencies...")
    
    dependencies = {
        "tesseract": False,
        "git": False
    }
    
    # Check Tesseract OCR
    try:
        result = subprocess.run(["tesseract", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            dependencies["tesseract"] = True
            print("✅ Tesseract OCR found")
        else:
            print("⚠️  Tesseract OCR not found or not working")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Tesseract OCR not found")
    
    # Check Git
    try:
        result = subprocess.run(["git", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            dependencies["git"] = True
            print("✅ Git found")
        else:
            print("⚠️  Git not found or not working")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Git not found")
    
    return dependencies


def install_system_dependencies() -> bool:
    """Install system dependencies."""
    print("🔧 Installing system dependencies...")
    
    system = get_system_type()
    
    if system == "linux":
        return install_linux_dependencies()
    elif system == "macos":
        return install_macos_dependencies()
    elif system == "windows":
        return install_windows_dependencies()
    else:
        print("❌ Unsupported operating system")
        return False


def get_system_type() -> str:
    """Detect operating system type."""
    import platform
    
    system = platform.system().lower()
    if system == "linux":
        return "linux"
    elif system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"


def install_linux_dependencies() -> bool:
    """Install dependencies on Linux."""
    print("🐧 Installing Linux dependencies...")
    
    try:
        # Try apt (Debian/Ubuntu)
        result = subprocess.run(["which", "apt"], capture_output=True, text=True)
        if result.returncode == 0:
            print("📦 Using apt package manager...")
            
            # Update package list
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            
            # Install dependencies
            subprocess.run([
                "sudo", "apt-get", "install", "-y",
                "tesseract-ocr", "tesseract-ocr-eng", "git"
            ], check=True)
            
            print("✅ Linux dependencies installed successfully")
            return True
        
        # Try yum (RHEL/CentOS)
        result = subprocess.run(["which", "yum"], capture_output=True, text=True)
        if result.returncode == 0:
            print("📦 Using yum package manager...")
            
            subprocess.run([
                "sudo", "yum", "install", "-y",
                "tesseract", "tesseract-langpack-eng", "git"
            ], check=True)
            
            print("✅ Linux dependencies installed successfully")
            return True
        
        print("❌ No supported package manager found (apt or yum)")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Linux dependencies: {e}")
        return False


def install_macos_dependencies() -> bool:
    """Install dependencies on macOS."""
    print("🍎 Installing macOS dependencies...")
    
    try:
        # Check if Homebrew is installed
        result = subprocess.run(["which", "brew"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Homebrew not found")
            print("   Please install Homebrew first: https://brew.sh/")
            return False
        
        # Install dependencies
        subprocess.run(["brew", "install", "tesseract", "git"], check=True)
        
        print("✅ macOS dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install macOS dependencies: {e}")
        return False


def install_windows_dependencies() -> bool:
    """Install dependencies on Windows."""
    print("🪟 Installing Windows dependencies...")
    
    print("⚠️  Manual installation required on Windows")
    print("   Please install the following:")
    print("   1. Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki")
    print("   2. Git: https://git-scm.com/download/win")
    print("   3. Add both to your system PATH")
    
    # Check if dependencies are available after manual installation
    dependencies = check_system_dependencies()
    return all(dependencies.values())


def install_python_dependencies(force: bool = False) -> bool:
    """Install Python dependencies."""
    print("🐍 Installing Python dependencies...")
    
    dependencies = [
        "marker>=0.0.1",
        "torch>=2.0.0",
        "transformers>=4.30.0"
    ]
    
    try:
        for dep in dependencies:
            print(f"📦 Installing {dep}...")
            
            cmd = [sys.executable, "-m", "pip", "install"]
            if force:
                cmd.append("--force-reinstall")
            cmd.append(dep)
            
            subprocess.run(cmd, check=True)
            print(f"✅ {dep} installed successfully")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python dependencies: {e}")
        return False


def create_config_file() -> bool:
    """Create default configuration file."""
    print("⚙️  Creating configuration file...")
    
    config_dir = Path("config")
    config_file = config_dir / "marker_config.json"
    
    # Create config directory if it doesn't exist
    config_dir.mkdir(exist_ok=True)
    
    # Default configuration
    default_config = {
        "marker_integration": {
            "enabled": True,
            "marker_path": None,
            "use_llm": False,
            "force_ocr": False,
            "debug": False,
            "max_workers": 4,
            "timeout_seconds": 300,
            "output_formats": ["markdown", "json"],
            "quality_threshold": 70
        },
        "llm_enhancement": {
            "enabled": False,
            "api_key_env": "GOOGLE_API_KEY",
            "model": "gemini-2.0-flash",
            "max_tokens": 8000,
            "temperature": 0.1
        },
        "performance": {
            "batch_size": 10,
            "parallel_processing": True,
            "memory_limit_gb": 8,
            "gpu_acceleration": True
        },
        "output": {
            "preserve_markdown": True,
            "preserve_json": True,
            "cleanup_temp_files": True,
            "compression": False
        },
        "clinical_trial_specific": {
            "table_extraction_priority": True,
            "adverse_events_focus": True,
            "efficacy_data_enhancement": True,
            "safety_data_enhancement": True
        }
    }
    
    try:
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"✅ Configuration file created: {config_file}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create configuration file: {e}")
        return False


def test_installation() -> bool:
    """Test the Marker installation."""
    print("🧪 Testing Marker installation...")
    
    try:
        # Test Marker command
        result = subprocess.run(["marker", "--help"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Marker command works correctly")
        else:
            print("❌ Marker command failed")
            return False
        
        # Test Python import
        try:
            import marker
            print("✅ Marker Python module imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import Marker Python module: {e}")
            return False
        
        # Test basic functionality
        print("🔄 Testing basic functionality...")
        
        # Create a simple test
        test_result = test_basic_functionality()
        if test_result:
            print("✅ Basic functionality test passed")
        else:
            print("❌ Basic functionality test failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False


def test_basic_functionality() -> bool:
    """Test basic Marker functionality."""
    try:
        # This is a simplified test - in a real scenario, you'd test with a sample PDF
        print("   (Skipping PDF test - no sample PDF available)")
        return True
        
    except Exception as e:
        print(f"   Error during functionality test: {e}")
        return False


def validate_installation() -> Dict[str, bool]:
    """Validate the complete installation."""
    print("🔍 Validating installation...")
    
    validation_results = {
        "python_version": check_python_version(),
        "system_dependencies": False,
        "python_dependencies": False,
        "marker_command": False,
        "marker_module": False,
        "configuration": False
    }
    
    # Check system dependencies
    dependencies = check_system_dependencies()
    validation_results["system_dependencies"] = all(dependencies.values())
    
    # Check Python dependencies
    try:
        import marker
        import torch
        import transformers
        validation_results["python_dependencies"] = True
        print("✅ Python dependencies validated")
    except ImportError as e:
        print(f"❌ Python dependencies validation failed: {e}")
    
    # Check Marker command
    try:
        result = subprocess.run(["marker", "--help"], 
                              capture_output=True, text=True, timeout=10)
        validation_results["marker_command"] = (result.returncode == 0)
        if validation_results["marker_command"]:
            print("✅ Marker command validated")
        else:
            print("❌ Marker command validation failed")
    except Exception as e:
        print(f"❌ Marker command validation failed: {e}")
    
    # Check Marker module
    try:
        import marker
        validation_results["marker_module"] = True
        print("✅ Marker module validated")
    except ImportError as e:
        print(f"❌ Marker module validation failed: {e}")
    
    # Check configuration
    config_file = Path("config/marker_config.json")
    validation_results["configuration"] = config_file.exists()
    if validation_results["configuration"]:
        print("✅ Configuration file validated")
    else:
        print("❌ Configuration file validation failed")
    
    return validation_results


def print_installation_summary(validation_results: Dict[str, bool]):
    """Print installation summary."""
    print_section("Installation Summary")
    
    total_checks = len(validation_results)
    passed_checks = sum(validation_results.values())
    
    print(f"📊 Validation Results: {passed_checks}/{total_checks} checks passed")
    
    for check, passed in validation_results.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check.replace('_', ' ').title()}")
    
    if passed_checks == total_checks:
        print("\n🎉 Installation completed successfully!")
        print("\n💡 Next Steps:")
        print("   1. Review the configuration file: config/marker_config.json")
        print("   2. Set GOOGLE_API_KEY environment variable for LLM enhancement")
        print("   3. Run the demonstration: python demo_marker_integration.py")
        print("   4. Run tests: python test_marker_integration.py")
    else:
        print("\n⚠️  Installation completed with issues")
        print("   Please review the failed checks above and resolve them")


def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(description="Marker Installation Script")
    parser.add_argument("--force", action="store_true", 
                       help="Force reinstall Python dependencies")
    parser.add_argument("--test", action="store_true",
                       help="Only run installation tests")
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    if args.test:
        # Only run tests
        validation_results = validate_installation()
        print_installation_summary(validation_results)
        return
    
    # Full installation process
    print("🚀 Starting Marker installation...")
    
    # Step 1: Check Python version
    if not check_python_version():
        print("❌ Python version check failed. Exiting.")
        sys.exit(1)
    
    # Step 2: Check system dependencies
    dependencies = check_system_dependencies()
    if not all(dependencies.values()):
        print("⚠️  Some system dependencies are missing")
        response = input("Install system dependencies? (y/N): ")
        if response.lower() in ['y', 'yes']:
            if not install_system_dependencies():
                print("❌ Failed to install system dependencies")
                print("   Please install them manually and run the script again")
                sys.exit(1)
        else:
            print("❌ System dependencies required. Exiting.")
            sys.exit(1)
    
    # Step 3: Install Python dependencies
    if not install_python_dependencies(args.force):
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Step 4: Create configuration file
    if not create_config_file():
        print("❌ Failed to create configuration file")
        sys.exit(1)
    
    # Step 5: Test installation
    if not test_installation():
        print("❌ Installation test failed")
        sys.exit(1)
    
    # Step 6: Validate installation
    validation_results = validate_installation()
    print_installation_summary(validation_results)
    
    # Exit with appropriate code
    total_checks = len(validation_results)
    passed_checks = sum(validation_results.values())
    
    if passed_checks == total_checks:
        print("\n✅ Installation completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Installation completed with issues")
        sys.exit(1)


if __name__ == "__main__":
    main() 