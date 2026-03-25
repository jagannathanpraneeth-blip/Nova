import os
import subprocess
import webbrowser
import logging
import json
import re
import time
import pyautogui
from typing import Dict, Any
from modules.pyautogui_config import safe_click, safe_type, safe_press, safe_hotkey

class AutomationWorkflows:
    """
    High-level automation workflows for common tasks like sending WhatsApp messages,
    emails, taking screenshots, etc.
    """
    
    def __init__(self, tts_engine):
        self.logger = logging.getLogger('AutomationWorkflows')
        self.tts = tts_engine
    
    def send_whatsapp_message(self, contact: str, message: str) -> Dict[str, Any]:
        """Send WhatsApp message via WhatsApp Web"""
        try:
            self.tts.speak(f"Sending WhatsApp message to {contact}")
            
            # URL encode the message
            import urllib.parse
            encoded_message = urllib.parse.quote(message)
            
            # Open WhatsApp Web with pre-filled message
            url = f"https://web.whatsapp.com/send?text={encoded_message}"
            if contact:
                # If contact name/number provided, add it
                url = f"https://web.whatsapp.com/send?phone={contact}&text={encoded_message}"
            
            webbrowser.open(url)
            
            # Wait for page to load
            time.sleep(5)
            
            # Press Enter to send (after WhatsApp Web loads)
            self.tts.speak("Please wait while I open WhatsApp Web")
            time.sleep(3)
            safe_press('enter')
            
            self.tts.speak("Message sent")
            return {"success": True, "message": f"Sent to {contact}", "action": "whatsapp_send"}
            
        except Exception as e:
            self.logger.error(f"WhatsApp error: {e}")
            self.tts.speak("Failed to send WhatsApp message")
            return {"success": False, "message": str(e), "action": "whatsapp_error"}
    
    def take_screenshot(self, filename: str = None) -> Dict[str, Any]:
        """Take a screenshot and save it"""
        try:
            if not filename:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            # Ensure .png extension
            if not filename.endswith('.png'):
                filename += '.png'
            
            # Save to Desktop
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            filepath = os.path.join(desktop, filename)
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            self.tts.speak(f"Screenshot saved to Desktop as {filename}")
            return {"success": True, "message": f"Saved as {filename}", "action": "screenshot"}
            
        except Exception as e:
            self.logger.error(f"Screenshot error: {e}")
            self.tts.speak("Failed to take screenshot")
            return {"success": False, "message": str(e), "action": "screenshot_error"}
    
    def open_gmail_compose(self, to: str = "", subject: str = "", body: str = "") -> Dict[str, Any]:
        """Open Gmail compose window with pre-filled fields"""
        try:
            import urllib.parse
            
            # Build Gmail compose URL
            url = "https://mail.google.com/mail/?view=cm&fs=1"
            if to:
                url += f"&to={urllib.parse.quote(to)}"
            if subject:
                url += f"&su={urllib.parse.quote(subject)}"
            if body:
                url += f"&body={urllib.parse.quote(body)}"
            
            webbrowser.open(url)
            self.tts.speak("Opening Gmail compose")
            return {"success": True, "message": "Gmail opened", "action": "gmail_compose"}
            
        except Exception as e:
            self.logger.error(f"Gmail error: {e}")
            self.tts.speak("Failed to open Gmail")
            return {"success": False, "message": str(e), "action": "gmail_error"}
    
    def set_reminder(self, reminder_text: str, minutes: int = 5) -> Dict[str, Any]:
        """Set a reminder using Windows Task Scheduler"""
        try:
            import datetime
            
            # Calculate time
            reminder_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
            time_str = reminder_time.strftime("%H:%M")
            
            # Create a simple notification using msg command
            msg_text = f"Reminder: {reminder_text}"
            
            # Use PowerShell to schedule a notification
            ps_command = f'''
            Start-Sleep -Seconds {minutes * 60}
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.MessageBox]::Show("{msg_text}", "Nova Reminder")
            '''
            
            # Run in background
            subprocess.Popen(['powershell', '-Command', ps_command], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            self.tts.speak(f"Reminder set for {minutes} minutes from now")
            return {"success": True, "message": f"Reminder in {minutes} min", "action": "reminder"}
            
        except Exception as e:
            self.logger.error(f"Reminder error: {e}")
            self.tts.speak("Failed to set reminder")
            return {"success": False, "message": str(e), "action": "reminder_error"}
    
    def play_youtube_video(self, search_query: str) -> Dict[str, Any]:
        """Search and play a YouTube video"""
        try:
            import urllib.parse
            from modules.pyautogui_config import safe_click
            
            query = urllib.parse.quote(search_query)
            url = f"https://www.youtube.com/results?search_query={query}"
            
            webbrowser.open(url)
            self.tts.speak(f"Playing {search_query} on YouTube")
            
            # Wait for page to fully load (YouTube can be slow)
            self.logger.info("Waiting for YouTube to load...")
            time.sleep(7)  # Longer wait for better reliability
            
            # Get screen size for responsive positioning
            screen_width, screen_height = pyautogui.size()
            self.logger.info(f"Screen: {screen_width}x{screen_height}")
            
            # Calculate click position based on screen size
            # YouTube first video is typically at these percentages
            # Optimized for 1920x1080 and other common resolutions
            click_x = int(screen_width * 0.28)  # 28% from left
            click_y = int(screen_height * 0.37)  # 37% from top
            
            self.logger.info(f"Clicking video at ({click_x}, {click_y})...")
            
            # Double-click for better reliability
            # Sometimes single click doesn't register
            safe_click(click_x, click_y, clicks=2, interval=0.5)
            
            # Wait for video to start
            time.sleep(2)
            
            self.logger.info("Video should be playing")
            self.tts.speak("Video is playing")
            return {"success": True, "message": f"Playing {search_query}", "action": "youtube_play"}
            
        except Exception as e:
            self.logger.error(f"YouTube error: {e}")
            # Don't report as failure - search is still open
            self.tts.speak("YouTube search opened. Click the video you want.")
            return {"success": True, "message": "Search opened", "action": "youtube_search"}
    
    def create_note(self, note_text: str) -> Dict[str, Any]:
        """Create a quick note in Notepad"""
        try:
            # Open Notepad
            subprocess.Popen(["notepad.exe"])
            time.sleep(1)
            
            # Type the note
            safe_type(note_text, interval=0.05)
            
            self.tts.speak("Note created in Notepad")
            return {"success": True, "message": "Note created", "action": "note_create"}
            
        except Exception as e:
            self.logger.error(f"Note error: {e}")
            self.tts.speak("Failed to create note")
            return {"success": False, "message": str(e), "action": "note_error"}
    
    def google_search_and_read(self, query: str) -> Dict[str, Any]:
        """Search Google and read the first result snippet"""
        try:
            import urllib.parse
            
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            
            webbrowser.open(url)
            self.tts.speak(f"Searching for {query}")
            
            return {"success": True, "message": f"Searched: {query}", "action": "google_search"}
            
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return {"success": False, "message": str(e), "action": "search_error"}
    
    def minimize_all_windows(self) -> Dict[str, Any]:
        """Minimize all windows (show desktop)"""
        try:
            safe_hotkey('win', 'd')
            self.tts.speak("Minimized all windows")
            return {"success": True, "message": "Desktop shown", "action": "minimize_all"}
        except Exception as e:
            return {"success": False, "message": str(e), "action": "minimize_error"}
    
    def maximize_window(self) -> Dict[str, Any]:
        """Maximize current window"""
        try:
            safe_hotkey('win', 'up')
            self.tts.speak("Window maximized")
            return {"success": True, "message": "Maximized", "action": "maximize"}
        except Exception as e:
            return {"success": False, "message": str(e), "action": "maximize_error"}
    
    def close_current_window(self) -> Dict[str, Any]:
        """Close the current active window"""
        try:
            safe_hotkey('alt', 'f4')
            self.tts.speak("Closing window")
            return {"success": True, "message": "Window closed", "action": "close_window"}
        except Exception as e:
            return {"success": False, "message": str(e), "action": "close_error"}

    def run_automation_template(self, template_name: str) -> Dict[str, Any]:
        """Run a predefined automation template"""
        template_name = template_name.lower()
        self.logger.info(f"Running template: {template_name}")
        
        if "weekly report" in template_name:
            return self._template_weekly_report()
        elif "morning startup" in template_name or "start work" in template_name:
            return self._template_morning_startup()
        else:
            self.tts.speak(f"I don't have a template for {template_name}")
            return {"success": False, "message": "Unknown template", "action": "template_error"}

    def _template_weekly_report(self):
        try:
            self.tts.speak("Starting weekly report automation.")
            
            # 1. Open Excel (standard command)
            # using 'start excel' via shell usually works if installed
            subprocess.Popen("start excel", shell=True)
            self.tts.speak("Opening Excel...")
            time.sleep(5) # Wait for Excel to load (adjust as needed)
            
            # 2. Select Blank Workbook (usually selected by default, just press Enter)
            safe_press('enter')
            time.sleep(2)
            
            # 3. Fill headers
            headers = ["Date", "Task", "Status", "Hours", "Notes"]
            safe_type("Weekly Report: " + time.strftime("%Y-%m-%d"))
            safe_press('enter')
            safe_press('enter')
            
            for header in headers:
                safe_type(header)
                safe_press('tab')
            
            # Reset cursor
            safe_press('enter')
            safe_press('home')
            
            self.tts.speak("Excel template ready.")
            return {"success": True, "message": "Weekly report template executed", "action": "template_weekly_report"}
            
        except Exception as e:
            self.logger.error(f"Weekly report error: {e}")
            self.tts.speak("Something went wrong with the report template.")
            return {"success": False, "message": str(e), "action": "template_error"}

    def _template_morning_startup(self):
        try:
            self.tts.speak("Initiating morning startup sequence.")
            
            # 1. Open Chrome
            self.tts.speak("Opening Browser...")
            subprocess.Popen("start chrome", shell=True)
            time.sleep(3)
            
            # 2. Open Calendar
            webbrowser.open("https://calendar.google.com")
            
            # 3. Open Email (new tab)
            time.sleep(1)
            safe_hotkey('ctrl', 't')
            webbrowser.open("https://gmail.com")
            
            # 4. Open Notepad for todolist
            self.tts.speak("Opening Notepad for daily tasks...")
            subprocess.Popen("notepad.exe")
            time.sleep(1)
            safe_type(f"Tasks for {time.strftime('%A, %B %d')}:\n- ")
            
            self.tts.speak("Morning startup complete. Have a great day!")
            return {"success": True, "message": "Morning startup complete", "action": "template_morning_startup"}
            
        except Exception as e:
            self.logger.error(f"Startup error: {e}")
            return {"success": False, "message": str(e), "action": "template_error"}
