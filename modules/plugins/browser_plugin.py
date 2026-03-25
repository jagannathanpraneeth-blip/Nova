from modules.plugins.base import Plugin
import webbrowser
import time
import pyautogui
from modules.pyautogui_config import safe_hotkey, safe_type, safe_press

class BrowserPlugin(Plugin):
    def handle_command(self, text):
        if "download" in text and ("docs" in text or "documentation" in text):
            return self.download_docs(text)
        return None

    def download_docs(self, text):
        """
        Downloads documentation.
        "Nova download react docs."
        """
        # Extract what to download
        query = text.replace("download", "").replace("docs", "").replace("documentation", "").strip()
        
        self.core.tts.speak(f"Searching for {query} documentation.")
        
        # 1. Open browser and search
        url = f"https://www.google.com/search?q={query}+documentation+pdf"
        webbrowser.open(url)
        time.sleep(4) # Wait for load
        
        # 2. Navigate (Click first result - simplified)
        # We'll assume the user wants to see the page first
        self.core.tts.speak("Opening the first result.")
        
        # Click coordinates (approximate for Google first result)
        screen_width, screen_height = pyautogui.size()
        click_x = int(screen_width * 0.25)
        click_y = int(screen_height * 0.35)
        pyautogui.click(click_x, click_y)
        
        time.sleep(4) # Wait for page load
        
        # 3. Save PDF or Page
        self.core.tts.speak("Saving the page.")
        safe_hotkey('ctrl', 'p') # Print dialog
        time.sleep(2)
        safe_press('enter') # Click Print/Save
        time.sleep(1)
        
        # Type name
        filename = f"{query}_docs"
        safe_type(filename)
        time.sleep(0.5)
        safe_press('enter') # Save
        
        # 4. Close tab
        time.sleep(2)
        self.core.tts.speak("Closing the tab.")
        safe_hotkey('ctrl', 'w')
        
        return {"success": True, "message": f"Downloaded {query} docs", "action": "download_docs"}
