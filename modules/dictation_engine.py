import logging
import pyautogui
import time
from typing import Dict, Any, Optional
import threading
from modules.pyautogui_config import safe_type, safe_press, safe_hotkey

class DictationEngine:
    """
    Continuous dictation mode - types everything you say in real-time.
    Includes smart punctuation, commands, and formatting.
    NOTE: Dictation is currently disabled to avoid conflicts with main voice loop.
    Use "Nova, type [text]" for one-time typing instead.
    """
    
    def __init__(self, speech_engine, tts_engine):
        self.logger = logging.getLogger('DictationEngine')
        self.speech_engine = speech_engine
        self.tts = tts_engine
        self.is_active = False
        
    def start_dictation(self) -> Dict[str, Any]:
        """Start dictation mode - currently disabled"""
        self.tts.speak("Dictation mode is temporarily disabled. Use 'type' command instead.")
        return {"success": False, "message": "Dictation disabled - use 'type' command", "action": "dictation_disabled"}
    
    def stop_dictation(self) -> Dict[str, Any]:
        """Stop dictation mode"""
        return {"success": True, "message": "Dictation not active", "action": "dictation_inactive"}
    
    def is_dictation_active(self) -> bool:
        """Check if dictation mode is currently active"""
        return False
    
    def type_with_voice(self, text: str, auto_send: bool = False) -> Dict[str, Any]:
        """
        One-time voice typing - type the given text once.
        
        Args:
            text: Text to type
            auto_send: If True, press Enter after typing
        """
        try:
            time.sleep(1)  # Give user time to focus window
            
            # Use safe typing with better interval
            safe_type(text, interval=0.03)
            
            if auto_send:
                safe_press('enter')
            
            self.tts.speak("Done typing")
            return {"success": True, "message": "Text typed", "action": "voice_type"}
            
        except Exception as e:
            self.logger.error(f"Voice typing error: {e}")
            self.tts.speak("Failed to type")
            return {"success": False, "message": str(e), "action": "type_error"}
