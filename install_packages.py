#!/usr/bin/env python3
"""
Script to install missing packages required for the MCP agent.
Run this script to ensure all required packages are installed.
"""
import sys
import subprocess
import pkg_resources

def get_missing_packages():
    """Check for missing packages from requirements.txt"""
    required = {}
    with open('requirements.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Parse package names and version constraints
            parts = line.split('>=')
            if len(parts) == 2:
                package, version = parts
                required[package] = version
            else:
                package = line
                required[package] = None
    
    installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    missing = []
    
    for package in required:
        if package.lower() not in installed:
            requirement = package
            if required[package]:
                requirement += f">={required[package]}"
            missing.append(requirement)
    
    return missing

def install_packages(packages):
    """Install missing packages using pip"""
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Successfully installed {package}")
        except Exception as e:
            print(f"❌ Failed to install {package}: {str(e)}")
            
    # Special case for mcp which might need to be installed with different names
    if "mcp" in packages:
        try:
            print("Trying alternative installation for mcp package...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "model-context-protocol"])
            print("✅ Successfully installed model-context-protocol")
        except Exception as e:
            print(f"❌ Failed to install model-context-protocol: {str(e)}")

if __name__ == "__main__":
    print("Checking for missing packages...")
    missing = get_missing_packages()
    
    if missing:
        print(f"Found {len(missing)} missing packages:")
        for pkg in missing:
            print(f"  - {pkg}")
        
        install = input("Do you want to install these packages? (y/n): ").lower()
        if install == 'y' or install == 'yes':
            install_packages(missing)
            print("Installation complete!")
        else:
            print("Installation cancelled.")
    else:
        print("All required packages are already installed!") 