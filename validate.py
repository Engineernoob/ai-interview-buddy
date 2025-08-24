#!/usr/bin/env python3
"""
Validation script to check for common issues in the AI Interview Buddy project
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_file_exists(path, description):
    """Check if a file exists"""
    if os.path.exists(path):
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description}")
        return False

def check_python_imports():
    """Check if Python imports work"""
    print("\n🔍 Checking Python backend imports...")
    
    try:
        sys.path.insert(0, 'backend')
        from services.transcription import transcribe_segment
        from services.intent import detect_intent  
        from services.retriever import retrieve_context
        from services.llm import generate_suggestions
        print("✅ All Python imports working")
        return True
    except ImportError as e:
        print(f"❌ Python import error: {e}")
        return False

def check_package_json():
    """Check if package.json is valid"""
    print("\n🔍 Checking frontend package.json...")
    
    try:
        with open('frontend/package.json', 'r') as f:
            data = json.load(f)
        print("✅ package.json is valid JSON")
        
        required_deps = ['next', 'react', 'react-dom', 'tailwindcss']
        missing = [dep for dep in required_deps if dep not in data.get('dependencies', {})]
        
        if missing:
            print(f"❌ Missing dependencies: {missing}")
            return False
        else:
            print("✅ All required dependencies present")
            return True
            
    except Exception as e:
        print(f"❌ package.json error: {e}")
        return False

def check_node_modules():
    """Check if node_modules exists"""
    if os.path.exists('frontend/node_modules'):
        print("✅ Frontend dependencies installed")
        return True
    else:
        print("❌ Frontend dependencies not installed - run: cd frontend && npm install")
        return False

def check_python_venv():
    """Check if Python virtual environment exists and has dependencies"""
    if os.path.exists('backend/venv'):
        print("✅ Python virtual environment exists")
        
        # Check if requirements are installed
        try:
            result = subprocess.run([
                'backend/venv/bin/pip', 'list'
            ], capture_output=True, text=True, cwd='.')
            
            if 'fastapi' in result.stdout:
                print("✅ Python dependencies installed")
                return True
            else:
                print("❌ Python dependencies not installed - run: cd backend && pip install -r requirements.txt")
                return False
                
        except Exception as e:
            print(f"❌ Error checking Python dependencies: {e}")
            return False
    else:
        print("❌ Python virtual environment not found - run: cd backend && python -m venv venv")
        return False

def main():
    """Main validation function"""
    print("🚀 Validating AI Interview Buddy Project Setup\n")
    
    # Change to project root
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    issues = []
    
    print("📁 Checking file structure...")
    required_files = [
        ('backend/main.py', 'Backend main file'),
        ('backend/requirements.txt', 'Backend requirements'),
        ('backend/services/__init__.py', 'Backend services module'),
        ('backend/services/transcription.py', 'Transcription service'), 
        ('backend/services/intent.py', 'Intent detection service'),
        ('backend/services/retriever.py', 'Context retriever service'),
        ('backend/services/llm.py', 'LLM service'),
        ('frontend/package.json', 'Frontend package config'),
        ('frontend/app/page.tsx', 'Frontend home page'),
        ('frontend/app/interview/page.tsx', 'Frontend interview page'),
        ('frontend/components/CoachCard.tsx', 'Coach card component'),
        ('frontend/lib/audioStream.ts', 'Audio stream utility'),
    ]
    
    for file_path, desc in required_files:
        if not check_file_exists(file_path, desc):
            issues.append(f"Missing file: {file_path}")
    
    # Check Python imports
    if not check_python_imports():
        issues.append("Python import issues")
    
    # Check package.json
    if not check_package_json():
        issues.append("Frontend package.json issues")
    
    # Check dependencies
    if not check_node_modules():
        issues.append("Frontend dependencies not installed")
        
    if not check_python_venv():
        issues.append("Backend dependencies not installed")
    
    # Summary
    print(f"\n📋 Validation Summary:")
    if issues:
        print(f"❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"   • {issue}")
        print(f"\n🔧 Run ./setup.sh to fix dependency issues")
        return 1
    else:
        print("✅ All checks passed! Project should work correctly.")
        print("\n🚀 To start the application:")
        print("   1. Start Ollama: ollama serve")  
        print("   2. Start app: ./start-dev.sh")
        return 0

if __name__ == "__main__":
    sys.exit(main())