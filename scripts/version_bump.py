#!/usr/bin/env python3
"""
Simple script to bump version and display current version
"""
import json
import os
import sys

def bump_version():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, '..'))
        version_file = os.path.join(project_root, 'version.json')
        
        # Read current version
        with open(version_file, 'r') as f:
            data = json.load(f)
        
        # Bump patch version
        data['patch'] = int(data.get('patch', 0)) + 1
        
        # Write back to file
        with open(version_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Format version string
        version = f"{data['major']}.{data['minor']}.{data['patch']}"
        if data.get('pre'):
            version += f"-{data['pre']}"

        # Update version in GlowStatus.nuspec
        nuspec_path = os.path.join(project_root, 'GlowStatus.nuspec')
        if os.path.exists(nuspec_path):
            try:
                with open(nuspec_path, 'r', encoding='utf-8') as f:
                    nuspec = f.read()
                import re
                nuspec_new = re.sub(r'<version>.*?</version>', f'<version>{version}</version>', nuspec, count=1)
                with open(nuspec_path, 'w', encoding='utf-8') as f:
                    f.write(nuspec_new)
            except Exception as e:
                print(f"Warning: Could not update nuspec version: {e}")

        print(f"Building GlowStatus version: {version}")
        return True
        
    except Exception as e:
        print(f"Error bumping version: {e}")
        return False

if __name__ == "__main__":
    if not bump_version():
        sys.exit(1)