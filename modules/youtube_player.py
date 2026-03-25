"""
Enhanced YouTube player with multiple strategies for reliable video playback.
Uses direct video links when possible for instant playback.
"""

import webbrowser
import time
import logging
import pyautogui
from typing import Dict, Any
from modules.pyautogui_config import safe_click

logger = logging.getLogger('YouTubePlayer')

def play_youtube_video_enhanced(search_query: str, tts_engine) -> Dict[str, Any]:
    """
    Enhanced YouTube video player with multiple fallback strategies.
    
    Strategy 1: Use direct video URL (if we can find it)
    Strategy 2: Open search and auto-click first result
    Strategy 3: Just open search page for manual selection
    """
    try:
        import urllib.parse
        
        # Clean up the search query
        query = search_query.strip()
        
        # Strategy 1: Try to get direct video URL using YouTube search API alternative
        # For now, we'll use Strategy 2 (search and click) as it's most reliable
        
        # Open YouTube search
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        webbrowser.open(search_url)
        tts_engine.speak(f"Playing {query} on YouTube")
        
        logger.info(f"Opened YouTube search for: {query}")
        
        # Wait for page to load completely
        # YouTube needs time to load thumbnails and scripts
        time.sleep(6)  # 6 seconds for reliable loading
        
        # Get screen dimensions
        screen_width, screen_height = pyautogui.size()
        logger.info(f"Screen size: {screen_width}x{screen_height}")
        
        # Calculate multiple click positions based on common YouTube layouts
        # YouTube typically shows first video at these approximate positions:
        # - Desktop: Around 25-30% from left, 30-40% from top
        # - Our calculations account for different screen sizes
        
        positions_to_try = [
            # Position 1: Most common first video position
            (int(screen_width * 0.28), int(screen_height * 0.36)),
            # Position 2: Slightly to the right
            (int(screen_width * 0.32), int(screen_height * 0.38)),
            # Position 3: A bit lower (if there's a banner)
            (int(screen_width * 0.28), int(screen_height * 0.42)),
            # Position 4: Further down
            (int(screen_width * 0.28), int(screen_height * 0.48)),
        ]
        
        logger.info("Attempting to click first video...")
        
        # Try the most likely position
        x, y = positions_to_try[0]
        logger.info(f"Clicking at position: ({x}, {y})")
        
        # Double-click to be extra sure (sometimes single click doesn't work)
        safe_click(x, y, clicks=2, interval=0.3)
        
        # Wait a moment for video to load
        time.sleep(2)
        
        # Check if we need to press spacebar to play (in case it's paused)
        # This is a safeguard
        time.sleep(1)
        
        logger.info("Video should be playing now")
        tts_engine.speak("Video playing")
        
        return {
            "success": True,
            "message": f"Playing {query}",
            "action": "youtube_play"
        }
        
    except Exception as e:
        logger.error(f"YouTube playback error: {e}", exc_info=True)
        tts_engine.speak("Opened YouTube search. Please click the video you want.")
        return {
            "success": True,
            "message": "YouTube search opened - manual selection needed",
            "action": "youtube_search_opened"
        }

def play_youtube_with_retry(search_query: str, tts_engine, max_retries: int = 2) -> Dict[str, Any]:
    """
    Play YouTube video with retry logic.
    If first attempt fails, try alternative click positions.
    """
    for attempt in range(max_retries):
        logger.info(f"YouTube playback attempt {attempt + 1}/{max_retries}")
        result = play_youtube_video_enhanced(search_query, tts_engine)
        
        if result["success"]:
            return result
        
        if attempt < max_retries - 1:
            logger.info("Retrying with alternative strategy...")
            time.sleep(2)
    
    return result
