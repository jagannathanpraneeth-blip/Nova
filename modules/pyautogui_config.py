"""
PyAutoGUI configuration and initialization for safe and reliable automation.
This module sets up pyautogui with proper fail-safes and delays.
"""

import pyautogui
import logging

# Configure PyAutoGUI for optimal performance and safety
def configure_pyautogui():
    """Configure pyautogui with safe defaults"""
    logger = logging.getLogger('PyAutoGUI_Config')
    
    try:
        # FAILSAFE: Move mouse to top-left corner to abort
        pyautogui.FAILSAFE = True
        logger.info("PyAutoGUI FAILSAFE enabled (move mouse to corner to abort)")
        
        # PAUSE: Add small delay between pyautogui calls for reliability
        # 0.1 seconds is good - not too slow, but reliable
        pyautogui.PAUSE = 0.1
        logger.info(f"PyAutoGUI PAUSE set to {pyautogui.PAUSE}s")
        
        # Minimum PyAutoGUI pause for tweening
        pyautogui.MINIMUM_DURATION = 0.1
        
        # Get screen size for bounds checking
        screen_width, screen_height = pyautogui.size()
        logger.info(f"Screen size detected: {screen_width}x{screen_height}")
        
        logger.info("PyAutoGUI configured successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error configuring PyAutoGUI: {e}")
        return False

# Safe wrapper functions for common operations
def safe_click(x=None, y=None, clicks=1, button='left', interval=0.0):
    """Safe click with error handling - supports single, double, or multiple clicks"""
    try:
        if x is not None and y is not None:
            pyautogui.click(x, y, clicks=clicks, button=button, interval=interval)
        else:
            pyautogui.click(clicks=clicks, button=button, interval=interval)
        return True
    except Exception as e:
        logging.error(f"Click error: {e}")
        return False

def safe_type(text, interval=0.0):
    """Safe typing with error handling - supports all text including spaces"""
    try:
        # Use write() for general text - supports spaces and special chars
        pyautogui.write(text, interval=interval)
        return True
    except Exception as e:
        # Some chars might not work with write(), try typing each char manually
        try:
            for char in text:
                pyautogui.press(char) if len(char) == 1 else None
            return True
        except Exception as e2:
            logging.error(f"Type error: {e}, fallback also failed: {e2}")
            return False

def safe_press(key, presses=1, interval=0.0):
    """Safe key press with error handling"""
    try:
        pyautogui.press(key, presses=presses, interval=interval)
        return True
    except Exception as e:
        logging.error(f"Press error: {e}")
        return False

def safe_hotkey(*keys):
    """Safe hotkey combination with error handling"""
    try:
        pyautogui.hotkey(*keys)
        return True
    except Exception as e:
        logging.error(f"Hotkey error: {e}")
        return False

def safe_move(x, y, duration=0.5):
    """Safe mouse movement with error handling"""
    try:
        pyautogui.moveTo(x, y, duration=duration)
        return True
    except Exception as e:
        logging.error(f"Move error: {e}")
        return False

def safe_scroll(clicks):
    """Safe scroll with error handling"""
    try:
        pyautogui.scroll(clicks)
        return True
    except Exception as e:
        logging.error(f"Scroll error: {e}")
        return False

# Initialize on import
configure_pyautogui()
