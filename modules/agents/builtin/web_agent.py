"""
Nova Web Agent
==============
Handles web-related tasks: searching Google, navigation, playing YouTube videos.
"""

import webbrowser
import urllib.parse
import logging
import time
from typing import Dict, Any

from modules.agents.agent_base import Agent
from modules.pyautogui_config import safe_click


class WebAgent(Agent):
    """Agent responsible for all web-related operations."""

    def __init__(self, tts=None, **kwargs):
        super().__init__(
            name="WebAgent",
            description="Handles web tasks: searching the web, URL navigation, playing YouTube media.",
            **kwargs
        )
        self.tts = tts
        self.capabilities = ["web_search", "navigate_url", "youtube_play"]

    def _do_execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", "")
        params = task.get("parameters", {})
        raw_text = params.get("raw_text", task.get("original_text", ""))

        if action == "web_search":
            return self._web_search(params, raw_text)
        elif action == "navigate_url":
            return self._navigate_url(params, raw_text)
        elif action == "youtube_play":
            return self._youtube_play(params, raw_text)

        return {"success": False, "message": f"Unknown action: {action}", "action": action}

    def _web_search(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        query = params.get("query", "")
        if not query:
            for trigger in ["search for", "google", "search", "find", "look up"]:
                if trigger in raw_text.lower():
                    query = raw_text.lower().split(trigger, 1)[1].strip()
                    break
        if not query:
            query = raw_text

        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        msg = f"Searching Google for {query}"
        if self.tts:
            self.tts.speak(msg)
        return {"success": True, "message": msg, "action": "web_search"}

    def _navigate_url(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        url = params.get("url", "")
        if not url:
            for trigger in ["go to", "navigate to", "visit", "browse to"]:
                if trigger in raw_text.lower():
                    url = raw_text.lower().split(trigger, 1)[1].strip()
                    break
        if not url:
            url = raw_text.strip()

        if not url.startswith("http"):
            url = "https://" + url

        webbrowser.open(url)
        msg = f"Opening {url}"
        if self.tts:
            self.tts.speak(msg)
        return {"success": True, "message": msg, "action": "navigate_url"}

    def _youtube_play(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        query = params.get("query", "")
        if not query:
            query = raw_text
            for trigger in ["play", "youtube", "video", "song", "music"]:
                query = query.replace(trigger, "")
            query = query.strip()
        if not query:
            query = "music"

        import pyautogui
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        webbrowser.open(url)
        msg = f"Playing {query} on YouTube"
        if self.tts:
            self.tts.speak(msg)

        # Wait for YouTube search page to load
        time.sleep(7)

        # Click first video based on responsive percentages
        try:
            screen_width, screen_height = pyautogui.size()
            click_x = int(screen_width * 0.28)
            click_y = int(screen_height * 0.37)
            self.logger.info(f"Clicking YouTube video at ({click_x}, {click_y})")
            safe_click(click_x, click_y, clicks=2, interval=0.5)
            time.sleep(2)
            return {"success": True, "message": f"Playing {query}", "action": "youtube_play"}
        except Exception as e:
            self.logger.error(f"YouTube click failed: {e}")
            return {"success": True, "message": "Search opened on YouTube", "action": "youtube_search"}
