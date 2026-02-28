#!/usr/bin/env python
"""
UrbanSight - Quick Start Script
Run this file to start the server with one command
"""

import os
import sys
import subprocess
import webbrowser
import time

def main():
    print("="*60)
    print("  UrbanSight AI Surveillance System")
    print("  IIT Roorkee Changeathon Project")
    print("="*60)
    print()
    
    # Check if app.py exists
    if not os.path.exists('app.py'):
        print("❌ Error: app.py not found!")
        print("   Please run this script from the backend directory.")
        return
    
    # Install requirements if needed
    if not os.path.exists('venv'):
        print("📦 Setting up virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', 'venv'])
        
        # Activate and install
        if sys.platform == 'win32':
            pip_path = 'venv\\Scripts\\pip'
        else:
            pip_path = 'venv/bin/pip'
        
        subprocess.run([pip_path, 'install', '-r', 'requirements.txt'])
    
    print("🚀 Starting UrbanSight server...")
    print("   Dashboard will open automatically in 3 seconds...")
    print()
    
    # Open browser after delay
    def open_browser():
        time.sleep(3)
        webbrowser.open('http://localhost:5000')
        print("✅ Dashboard opened in browser")
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the server
    if sys.platform == 'win32':
        os.system('python app.py')
    else:
        os.system('python3 app.py')

if __name__ == '__main__':
    main()