#!/usr/bin/env python3
"""
NAVIGo Quick Setup and Run Script
This script helps you set up and run the NAVIGo application quickly
"""

import os
import sys
import subprocess
import platform

def print_header():
    print("=" * 60)
    print("🧭 NAVIGo - Intelligent Tourism System")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")

def check_folder_structure():
    """Verify folder structure exists"""
    required_folders = ['templates', 'static', 'static/css', 'static/js']
    missing_folders = []
    
    for folder in required_folders:
        if not os.path.exists(folder):
            missing_folders.append(folder)
            os.makedirs(folder, exist_ok=True)
    
    if missing_folders:
        print(f"✅ Created missing folders: {', '.join(missing_folders)}")
    else:
        print("✅ Folder structure verified")

def check_requirements():
    """Check if requirements.txt exists"""
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found!")
        print("   Please create requirements.txt with the required packages")
        sys.exit(1)
    print("✅ requirements.txt found")

def create_virtual_env():
    """Create virtual environment if it doesn't exist"""
    if not os.path.exists('venv'):
        print("\n📦 Creating virtual environment...")
        try:
            subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
            print("✅ Virtual environment created")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to create virtual environment")
            return False
    else:
        print("✅ Virtual environment exists")
        return False

def get_pip_command():
    """Get the appropriate pip command based on OS"""
    if platform.system() == 'Windows':
        return os.path.join('venv', 'Scripts', 'pip.exe')
    else:
        return os.path.join('venv', 'bin', 'pip')

def get_python_command():
    """Get the appropriate python command based on OS"""
    if platform.system() == 'Windows':
        return os.path.join('venv', 'Scripts', 'python.exe')
    else:
        return os.path.join('venv', 'bin', 'python')

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing required packages...")
    pip_cmd = get_pip_command()
    
    try:
        subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
        print("✅ All packages installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages")
        print("   Try running manually: pip install -r requirements.txt")
        sys.exit(1)

def check_api_keys():
    """Check if API keys are configured"""
    print("\n🔑 Checking API configuration...")
    
    with open('app.py', 'r') as f:
        content = f.read()
    
    if 'your_openweather_api_key' in content or 'your_google_maps_api_key' in content:
        print("⚠️  WARNING: Default API keys detected!")
        print("   Please update the following in app.py:")
        print("   - OPENWEATHER_API_KEY")
        print("   - GOOGLE_MAPS_API_KEY")
        print()
        print("   Get your free API keys:")
        print("   🌤️  OpenWeather: https://openweathermap.org/api")
        print("   🗺️  Google Maps: https://console.cloud.google.com/")
        print()
        
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    else:
        print("✅ API keys configured")

def run_application():
    """Run the Flask application"""
    print("\n🚀 Starting NAVIGo application...")
    print("=" * 60)
    print()
    print("📍 Application will be available at: http://127.0.0.1:5000/")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    python_cmd = get_python_command()
    
    try:
        subprocess.run([python_cmd, 'app.py'])
    except KeyboardInterrupt:
        print("\n\n👋 NAVIGo application stopped")
    except FileNotFoundError:
        print("❌ app.py not found!")
        print("   Please ensure app.py is in the current directory")
        sys.exit(1)

def main():
    """Main setup and run function"""
    print_header()
    
    # Check Python version
    check_python_version()
    
    # Check folder structure
    check_folder_structure()
    
    # Check requirements.txt
    check_requirements()
    
    # Create virtual environment
    new_venv = create_virtual_env()
    
    # Install requirements
    if new_venv:
        install_requirements()
    else:
        response = input("\n📦 Reinstall packages? (y/n): ")
        if response.lower() == 'y':
            install_requirements()
    
    # Check API keys
    check_api_keys()
    
    # Run application
    print()
    response = input("🚀 Ready to launch NAVIGo? (y/n): ")
    if response.lower() == 'y':
        run_application()
    else:
        print("\n👋 Setup complete! Run 'python setup_and_run.py' when ready to start.")

if __name__ == '__main__':
    main()