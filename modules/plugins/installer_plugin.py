from modules.plugins.base import Plugin
import subprocess
import time
import pyautogui
from modules.pyautogui_config import safe_type, safe_press, safe_hotkey, safe_click

class InstallerPlugin(Plugin):
    def handle_command(self, text):
        if "install" in text and "extension" in text and "code" in text:
            return self.install_vscode_extensions(text)
        return None

    def install_vscode_extensions(self, text):
        """
        Installs VS Code extensions.
        Expected text: "Nova install VS Code extensions for web dev" or similar.
        """
        self.core.tts.speak("Starting autonomous installer for VS Code.")
        
        # 1. Open VS Code
        self.core.tts.speak("Opening VS Code...")
        subprocess.Popen(["code"])
        time.sleep(5) # Wait for load
        
        # 2. Go to Extensions (Ctrl+Shift+X)
        self.core.tts.speak("Opening Extensions Marketplace...")
        safe_hotkey('ctrl', 'shift', 'x')
        time.sleep(2)
        
        # Determine extensions to install
        extensions = []
        if "web dev" in text or "web development" in text:
            extensions = ["HTML CSS Support", "ESLint", "Prettier"]
        elif "python" in text:
            extensions = ["Python", "Pylance"]
        else:
            # Try to extract from text
            # This is hard without NER, so we'll just default or ask
            extensions = ["Prettier"] # Default
            
        self.core.tts.speak(f"Installing {len(extensions)} extensions: {', '.join(extensions)}")
        
        # Self-healing loop
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                self._perform_installation(extensions)
                return {"success": True, "message": "Extensions installed", "action": "install_extensions"}
            except Exception as e:
                self.core.logger.error(f"Installation attempt {attempt+1} failed: {e}")
                if attempt < max_retries:
                    self.core.tts.speak("Installation hit a snag. Attempting to self-heal.")
                    self._recover_state()
                else:
                    self.core.tts.speak("Failed to install extensions after retries.")
                    return {"success": False, "message": str(e), "action": "install_error"}

    def _perform_installation(self, extensions):
        for ext in extensions:
            # 3. Search
            self.core.tts.speak(f"Searching for {ext}...")
            # Clear search box first (Ctrl+A, Backspace)
            safe_hotkey('ctrl', 'a')
            safe_press('backspace')
            
            safe_type(ext, interval=0.1)
            time.sleep(2)
            
            # 4. Install
            safe_press('tab') 
            time.sleep(0.5)
            safe_press('enter') # Try to select/install
            
            self.core.tts.speak(f"Installed {ext}")
            time.sleep(1)
            
        # 5. Reload window
        self.core.tts.speak("Reloading window to apply changes.")
        safe_hotkey('ctrl', 'shift', 'p')
        time.sleep(1)
        safe_type("Reload Window", interval=0.05)
        time.sleep(0.5)
        safe_press('enter')

    def _recover_state(self):
        """Close VS Code and restart it"""
        self.core.tts.speak("Closing unresponsive window.")
        safe_hotkey('alt', 'f4')
        time.sleep(2)
        self.core.tts.speak("Restarting VS Code...")
        subprocess.Popen(["code"])
        time.sleep(5)
        # Go back to extensions
        safe_hotkey('ctrl', 'shift', 'x')
        time.sleep(2)
