from modules.plugins.base import Plugin
from modules.utils import load_json, DATA_DIR
import os
import datetime
import webbrowser
import logging

class SocialMediaPlugin(Plugin):
    """
    Plugin for managing social media interactions with strict boundaries.
    """
    def __init__(self, core_system):
        super().__init__(core_system)
        self.logger = logging.getLogger('SocialMediaPlugin')
        self.policies_file = os.path.join(DATA_DIR, 'social_media_policies.json')
        self.policies = self._load_policies()
        
        # Usage tracking (In-memory for now, could be persisted)
        self.usage = {
            "whatsapp": {"messages_sent": 0},
            "instagram": {"dms_sent": 0}
        }

    def _load_policies(self):
        return load_json(self.policies_file)

    def get_intents(self):
        # This basic plugin registration might not be used if LLM decides, 
        # but provides a hook if we go back to keyword matching.
        return {
            "whatsapp_send": self.handle_whatsapp,
            "instagram_open": self.handle_instagram
        }
        
    def handle_command(self, text):
        # Called by AIBrain loop
        text = text.lower()
        if "whatsapp" in text:
            return self.handle_whatsapp(text)
        if "instagram" in text:
            return self.handle_instagram(text)
        return None

    def _check_permission(self, platform, action):
        """Check if an action is allowed by policy"""
        perms = self.policies.get("permissions", {}).get(platform, {})
        if not perms.get(action, False):
            self.logger.warning(f"Permission denied: {platform} -> {action}")
            return False, "Permission denied by safety policy."
            
        # Check boundaries (Time)
        bounds = self.policies.get("boundaries", {}).get(platform, {})
        allowed_hours = bounds.get("allowed_hours", {})
        now = datetime.datetime.now().hour
        if "start" in allowed_hours and "end" in allowed_hours:
            if not (allowed_hours["start"] <= now < allowed_hours["end"]):
                return False, f"Action allowed only between {allowed_hours['start']}:00 and {allowed_hours['end']}:00."
                
        # Check limits
        max_daily = bounds.get("max_messages_per_day", 100)
        current = 0
        if platform == "whatsapp":
            current = self.usage["whatsapp"]["messages_sent"]
        
        if current >= max_daily:
            return False, f"Daily limit of {max_daily} messages reached."
            
        return True, "Allowed"

    def handle_whatsapp(self, text):
        """Handle WhatsApp commands safely"""
        # "send whatsapp message to mom saying hello"
        
        # 1. PERMISSION CHECK
        allowed, msg = self._check_permission("whatsapp", "send_messages")
        if not allowed:
            self.core.tts.speak(f"I cannot do that. {msg}")
            return {"success": False, "message": msg, "action": "permission_denied"}

        # 2. Extract Info (Simplified)
        phone = ""
        message = ""
        
        # In a real app, we'd use contact book.
        # Here we just open the web interface and let user confirm/send or use pyautogui if requested.
        # Since user said "manage... with my permissions", let's assume we open the chat.
        
        self.core.tts.speak("Opening WhatsApp Web. Please confirm sending.")
        webbrowser.open("https://web.whatsapp.com/")
        
        # Increment usage
        self.usage["whatsapp"]["messages_sent"] += 1
        
        return {"success": True, "message": "Opened WhatsApp", "action": "open_whatsapp"}

    def handle_instagram(self, text):
        """Handle Instagram commands"""
        if "dm" in text or "message" in text:
            allowed, msg = self._check_permission("instagram", "send_dm")
            if not allowed:
                self.core.tts.speak(f"I cannot do that. {msg}")
                return {"success": False, "message": msg, "action": "permission_denied"}
                
            self.core.tts.speak("Opening Instagram Direct.")
            webbrowser.open("https://www.instagram.com/direct/inbox/")
            return {"success": True, "message": "Opened Instagram DM", "action": "open_instagram_dm"}
            
        elif "post" in text:
             allowed, msg = self._check_permission("instagram", "post_content")
             if not allowed:
                self.core.tts.speak(f"I cannot do that. {msg}")
                return {"success": False, "message": msg, "action": "permission_denied"}
        
        self.core.tts.speak("Opening Instagram.")
        webbrowser.open("https://www.instagram.com/")
        return {"success": True, "message": "Opened Instagram", "action": "open_instagram"}
