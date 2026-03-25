"""
Quick verification script to check if OpenAI API key is properly configured.
"""

import os
import sys

def check_api_key():
    """Check if OpenAI API key is set and valid"""
    
    print("=" * 60)
    print("    NOVA - API Key Verification")
    print("=" * 60)
    print()
    
    # Check in config file first
    api_key = None
    source = None
    
    try:
        import json
        config_path = os.path.join('data', 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                api_key = config.get('api_keys', {}).get('openai', '')
                if api_key and api_key != 'YOUR_OPENAI_API_KEY_HERE':
                    source = 'config.json'
                    print(f"✅ Found API key in: data/config.json")
    except Exception as e:
        print(f"⚠️  Could not read config.json: {e}")
    
    # Fall back to environment variable
    if not api_key or api_key == 'YOUR_OPENAI_API_KEY_HERE':
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            source = 'environment variable'
            print(f"✅ Found API key in: environment variable")
    
    if not api_key or api_key == 'YOUR_OPENAI_API_KEY_HERE':
        print("❌ OPENAI_API_KEY is NOT set!")
        print()
        print("This means either:")
        print("1. You didn't set it yet")
        print("2. You set it but didn't restart your terminal")
        print()
        print("SOLUTION:")
        print("1. Close this terminal/PowerShell window")
        print("2. Open a NEW terminal/PowerShell window")
        print("3. Run this script again: python check_api_key.py")
        print()
        print("OR run: python setup_api_key.py")
        print()
        return False
    
    # Key exists - validate format
    print("✅ OPENAI_API_KEY is set!")
    print()
    print(f"Key preview: {api_key[:10]}...{api_key[-4:]}")
    print(f"Length: {len(api_key)} characters")
    print()
    
    # Check if it starts with sk-
    if api_key.startswith('sk-'):
        print("✅ Key format looks correct (starts with 'sk-')")
    else:
        print("⚠️  Warning: Key should start with 'sk-'")
        print(f"   Your key starts with: {api_key[:5]}")
    
    print()
    
    # Test with a simple API call
    print("Testing API connection...")
    try:
        import openai
        
        # Set the key
        openai.api_key = api_key
        
        # Try a minimal API call
        print("Making test request to OpenAI...")
        
        # This is a minimal test - just checks if key is valid
        try:
            # Try to list models - cheap test
            client = openai.OpenAI(api_key=api_key)
            models = client.models.list()
            print("✅ API key is VALID! Connection successful!")
            print()
            print("=" * 60)
            print("    🎉 EVERYTHING IS WORKING PERFECTLY!")
            print("=" * 60)
            print()
            print("Nova's screen vision is ready to use!")
            print()
            print("Try these commands:")
            print('  "Nova, analyze screen"')
            print('  "Nova, read screen"')
            print('  "Nova, what do you see?"')
            print()
            return True
            
        except openai.AuthenticationError:
            print("❌ API key is INVALID!")
            print()
            print("The key is set, but OpenAI rejected it.")
            print("Please check that you copied the key correctly.")
            print()
            print("Run: python setup_api_key.py")
            print()
            return False
            
        except Exception as e:
            print(f"⚠️  Could not test API: {e}")
            print()
            print("The key is set, but we couldn't test it.")
            print("This might be a network issue.")
            print("Try running Nova anyway - it might work!")
            print()
            return True
            
    except ImportError:
        print("⚠️  openai package not installed")
        print()
        print("Installing now...")
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'openai'])
        print()
        print("Please run this script again: python check_api_key.py")
        return False
    
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print()
        print("The key is set, but we couldn't fully test it.")
        print("Try running Nova anyway!")
        print()
        return True

if __name__ == "__main__":
    try:
        success = check_api_key()
        if success:
            print("✅ You're all set! Run Nova with: python main.py")
            print()
    except KeyboardInterrupt:
        print("\n\nCheck cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTry running: python setup_api_key.py")
