import os
import logging
import pyautogui
import base64
from io import BytesIO
from typing import Dict, Any, Optional
import requests
import io
from PIL import Image

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class ScreenAnalyzer:
    """
    Captures and analyzes screen content using AI vision.
    Can describe what's on screen, read text, identify elements, etc.
    """
    
    def __init__(self, tts_engine):
        self.logger = logging.getLogger('ScreenAnalyzer')
        self.tts = tts_engine
        
        # Load API keys
        from modules.utils import load_api_keys
        keys = load_api_keys()
        
        self.provider = None
        
        # Check for Gemini Key (Prioritize if available/free)
        self.gemini_key = keys.get("gemini") or os.getenv("GEMINI_API_KEY")
        if self.gemini_key and GEMINI_AVAILABLE:
            self.provider = "gemini"
            genai.configure(api_key=self.gemini_key)
            self.logger.info("Using Gemini Vision")
            
        # Check for OpenAI Key
        self.openai_key = keys.get("openai") or os.getenv("OPENAI_API_KEY")
            
        if self.openai_key and self.openai_key != 'YOUR_OPENAI_API_KEY_HERE':
            if not self.provider: # Only set if Gemini not already picked
                self.provider = "openai"
                self.logger.info("Using OpenAI Vision")
        
        if not self.provider:
            self.logger.warning("No Vision API keys found (OpenAI or Gemini)")

        
    def capture_screen_to_base64(self) -> Optional[str]:
        """Capture current screen and convert to base64"""
        try:
            screenshot = pyautogui.screenshot()
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return img_str
        except Exception as e:
            self.logger.error(f"Screen capture error: {e}")
            return None
    
    def analyze_screen(self, prompt: str = "What do you see on this screen?") -> Dict[str, Any]:
        """
        Capture screen and analyze it using AI vision.
        
        Args:
            prompt: What to ask about the screen
            
        Returns:
            Dict with success status and analysis result
        """
        try:
            self.tts.speak("Analyzing your screen...")
            
            # Capture screen
            img_base64 = self.capture_screen_to_base64()
            if not img_base64:
                return {"success": False, "message": "Failed to capture screen", "action": "screen_error"}
            
            # If no API key, save screenshot and return
            if not self.provider:
                self.logger.warning("No Vision API key found. Saving screenshot only.")
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                filepath = os.path.join(desktop, "screen_capture.png")
                screenshot = pyautogui.screenshot()
                screenshot.save(filepath)
                
                msg = "Screen captured but AI analysis requires OpenAI or Gemini API key. Screenshot saved to Desktop."
                self.tts.speak(msg)
                return {"success": True, "message": msg, "action": "screen_captured"}
            
            # --- GEMINI ANALYSIS ---
            if self.provider == "gemini":
                try:
                    img_data = base64.b64decode(img_base64)
                    image = Image.open(io.BytesIO(img_data))
                    
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content([prompt, image])

                    analysis = response.text
                    
                    self.logger.info(f"Gemini Analysis: {analysis}")
                    self.tts.speak(analysis)
                    return {"success": True, "message": analysis, "action": "screen_analyzed"}
                except Exception as e:
                    self.logger.error(f"Gemini Error: {e}")
                    self.tts.speak("Gemini vision failed.")
                    return {"success": False, "message": str(e), "action": "analysis_error"}

            # --- OPENAI ANALYSIS ---
            if self.provider == "openai":
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_key}"
                }
                
                payload = {
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{img_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 500
                }
                
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result['choices'][0]['message']['content']
                    
                    self.logger.info(f"Screen analysis: {analysis}")
                    self.tts.speak(analysis)
                    
                    return {
                        "success": True,
                        "message": analysis,
                        "action": "screen_analyzed"
                    }
                elif response.status_code == 429:
                    error_msg = "Rate limit exceeded or insufficient quota"
                    self.logger.error(f"OpenAI API Error 429: {response.text}")
                    self.tts.speak("I'm currently out of AI credits. Please check your OpenAI API quota.")
                    return {"success": False, "message": "API Quota Exceeded", "action": "api_error_429"}
                else:
                    error_msg = f"API error: {response.status_code}"
                    self.logger.error(f"{error_msg} - {response.text}")
                    self.tts.speak(f"Failed to analyze screen. Error {response.status_code}")
                    return {"success": False, "message": error_msg, "action": "api_error"}
                
        except Exception as e:
            self.logger.error(f"Screen analysis error: {e}")
            self.tts.speak("Failed to analyze screen")
            return {"success": False, "message": str(e), "action": "analysis_error"}
    
    def read_screen_text(self) -> Dict[str, Any]:
        """Read and extract all text from the screen"""
        return self.analyze_screen("Read all the text visible on this screen and tell me what it says.")
    
    def describe_screen(self) -> Dict[str, Any]:
        """Describe what's currently on screen"""
        return self.analyze_screen("Describe what you see on this screen in detail.")
    
    def find_on_screen(self, item: str) -> Dict[str, Any]:
        """Find a specific item on screen"""
        return self.analyze_screen(f"Is there a {item} visible on this screen? If yes, describe its location and what it looks like.")
    
    def summarize_screen(self) -> Dict[str, Any]:
        """Provide a brief summary of screen content"""
        return self.analyze_screen("Provide a brief summary of what's on this screen.")
