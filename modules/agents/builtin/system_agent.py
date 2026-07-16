"""
Nova System Agent
=================
Handles system-level operations: opening/closing apps, system commands,
volume/brightness control, keyboard/mouse control, time/date queries.
"""

import os
import subprocess
import logging
import datetime
import time
from typing import Dict, Any

from modules.agents.agent_base import Agent
from modules.pyautogui_config import (safe_click, safe_type, safe_press,
                                       safe_hotkey, safe_move, safe_scroll)


class SystemAgent(Agent):
    """Agent responsible for all system-level interactions."""

    def __init__(self, tts=None, **kwargs):
        super().__init__(
            name="SystemAgent",
            description="Controls system operations: apps, keyboard, mouse, volume, system commands, time/date queries.",
            **kwargs
        )
        self.tts = tts
        self.capabilities = [
            "open_app", "close_app", "system_command",
            "volume_control", "brightness_control",
            "keyboard_control", "mouse_control",
            "type_text", "press_key",
            "system_info",  # time, date queries
        ]

        # Common app -> executable mapping
        self.app_map = {
            "chrome": "chrome.exe", "google chrome": "chrome.exe",
            "notepad": "notepad.exe", "calculator": "calc.exe",
            "calc": "calc.exe", "paint": "mspaint.exe",
            "word": "winword.exe", "excel": "excel.exe",
            "powerpoint": "powerpnt.exe", "cmd": "cmd.exe",
            "powershell": "powershell.exe", "explorer": "explorer.exe",
            "file explorer": "explorer.exe", "task manager": "taskmgr.exe",
            "control panel": "control.exe", "settings": "ms-settings:",
        }

        # Process name mapping for closing
        self.process_map = {
            "chrome": "chrome.exe", "notepad": "notepad.exe",
            "calculator": "calculator.exe", "calc": "calculator.exe",
        }

    def _do_execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", "")
        params = task.get("parameters", {})
        raw_text = params.get("raw_text", task.get("original_text", ""))

        dispatch = {
            "open_app": self._open_app,
            "close_app": self._close_app,
            "system_command": self._system_command,
            "volume_control": self._volume_control,
            "brightness_control": self._brightness_control,
            "keyboard_control": self._keyboard_control,
            "mouse_control": self._mouse_control,
            "type_text": self._type_text,
            "press_key": self._press_key,
            "system_info": self._system_info,
        }

        handler = dispatch.get(action)
        if handler:
            return handler(params, raw_text)

        return {"success": False, "message": f"Unknown action: {action}", "action": action}

    # ── App Control ───────────────────────────────────────────────────

    def _open_app(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        app_name = params.get("app_name", "")
        if not app_name:
            # Extract from raw text
            for trigger in ["open", "launch", "start", "run"]:
                if trigger in raw_text.lower():
                    app_name = raw_text.lower().split(trigger, 1)[1].strip()
                    break

        if not app_name:
            return {"success": False, "message": "No app specified", "action": "open_app"}

        if self.tts:
            self.tts.speak(f"Opening {app_name}")

        # Method 1: Known apps
        if app_name.lower() in self.app_map:
            try:
                executable = self.app_map[app_name.lower()]
                if executable.startswith("ms-"):
                    subprocess.Popen(["start", executable], shell=True)
                else:
                    subprocess.Popen([executable], shell=True)
                return {"success": True, "message": f"Opened {app_name}", "action": "open_app"}
            except Exception:
                pass

        # Method 2: Windows Search (universal)
        try:
            safe_press('win')
            time.sleep(0.5)
            safe_type(app_name, interval=0.01)
            time.sleep(0.8)
            safe_press('enter')
            return {"success": True, "message": f"Opened {app_name}", "action": "open_app"}
        except Exception as e:
            self.logger.error(f"Failed to open {app_name}: {e}")
            return {"success": False, "message": str(e), "action": "open_app"}

    def _close_app(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        app_name = params.get("app_name", "")
        if not app_name:
            for trigger in ["close", "kill", "stop", "exit"]:
                if trigger in raw_text.lower():
                    app_name = raw_text.lower().split(trigger, 1)[1].strip()
                    break

        process_name = self.process_map.get(app_name, app_name + ".exe")
        try:
            subprocess.run(["taskkill", "/F", "/IM", process_name],
                           check=True, capture_output=True)
            if self.tts:
                self.tts.speak(f"Closed {app_name}")
            return {"success": True, "message": f"Closed {app_name}", "action": "close_app"}
        except Exception as e:
            self.logger.error(f"Failed to close {app_name}: {e}")
            if self.tts:
                self.tts.speak(f"Couldn't close {app_name}")
            return {"success": False, "message": str(e), "action": "close_app"}

    # ── System Commands ───────────────────────────────────────────────

    def _system_command(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        command = params.get("command", raw_text.lower())

        if "shutdown" in command:
            if self.tts:
                self.tts.speak("Shutting down the system")
            subprocess.run(["shutdown", "/s", "/t", "10"])
            return {"success": True, "message": "Shutting down", "action": "shutdown"}
        elif "restart" in command:
            if self.tts:
                self.tts.speak("Restarting the system")
            subprocess.run(["shutdown", "/r", "/t", "10"])
            return {"success": True, "message": "Restarting", "action": "restart"}
        elif "sleep" in command:
            if self.tts:
                self.tts.speak("Putting system to sleep")
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return {"success": True, "message": "Sleep mode", "action": "sleep"}
        elif "lock" in command:
            if self.tts:
                self.tts.speak("Locking the system")
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            return {"success": True, "message": "Locked", "action": "lock"}

        return {"success": False, "message": "Unknown system command", "action": "system_command"}

    # ── Volume / Brightness ───────────────────────────────────────────

    def _volume_control(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        try:
            command = params.get("command", raw_text.lower())
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)

            if "mute" in command and "unmute" not in command:
                volume.SetMute(1, None)
                if self.tts:
                    self.tts.speak("Muted")
                return {"success": True, "message": "Muted", "action": "mute"}
            elif "unmute" in command:
                volume.SetMute(0, None)
                if self.tts:
                    self.tts.speak("Unmuted")
                return {"success": True, "message": "Unmuted", "action": "unmute"}
            elif "up" in command or "increase" in command:
                current = volume.GetMasterVolumeLevelScalar()
                volume.SetMasterVolumeLevelScalar(min(1.0, current + 0.1), None)
                if self.tts:
                    self.tts.speak("Volume up")
                return {"success": True, "message": "Volume increased", "action": "volume_up"}
            elif "down" in command or "decrease" in command:
                current = volume.GetMasterVolumeLevelScalar()
                volume.SetMasterVolumeLevelScalar(max(0.0, current - 0.1), None)
                if self.tts:
                    self.tts.speak("Volume down")
                return {"success": True, "message": "Volume decreased", "action": "volume_down"}

        except Exception as e:
            self.logger.error(f"Volume control error: {e}")
        return {"success": False, "message": "Volume control failed", "action": "volume_control"}

    def _brightness_control(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        try:
            import screen_brightness_control as sbc
            command = params.get("command", raw_text.lower())

            if "up" in command or "increase" in command:
                current = sbc.get_brightness()[0]
                sbc.set_brightness(min(100, current + 10))
                if self.tts:
                    self.tts.speak("Brightness increased")
                return {"success": True, "message": "Brightness up", "action": "brightness_up"}
            elif "down" in command or "decrease" in command:
                current = sbc.get_brightness()[0]
                sbc.set_brightness(max(0, current - 10))
                if self.tts:
                    self.tts.speak("Brightness decreased")
                return {"success": True, "message": "Brightness down", "action": "brightness_down"}
        except Exception as e:
            self.logger.error(f"Brightness error: {e}")
        return {"success": False, "message": "Brightness control failed", "action": "brightness_control"}

    # ── Keyboard Control ──────────────────────────────────────────────

    def _keyboard_control(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        text = raw_text.lower()
        try:
            # Key combos
            key_combo = params.get("key_combo", "")
            if key_combo:
                if "+" in key_combo:
                    import pyautogui
                    pyautogui.hotkey(*key_combo.split('+'))
                else:
                    safe_press(key_combo)
                return {"success": True, "message": f"Pressed {key_combo}", "action": "key_press"}

            # Common keys
            key_map = {
                "enter": "enter", "return": "enter", "escape": "esc", "esc": "esc",
                "space": "space", "spacebar": "space", "tab": "tab",
                "backspace": "backspace", "delete": "delete",
                "up arrow": "up", "arrow up": "up", "down arrow": "down",
                "arrow down": "down", "left arrow": "left", "right arrow": "right",
            }
            for keyword, key in key_map.items():
                if keyword in text:
                    safe_press(key)
                    if self.tts:
                        self.tts.speak(f"Pressed {keyword}")
                    return {"success": True, "message": f"Pressed {key}", "action": "key_press"}

            # Shortcuts
            shortcuts = [
                ("ctrl", "c", "copy", "Copied"), ("ctrl", "v", "paste", "Pasted"),
                ("ctrl", "x", "cut", "Cut"), ("ctrl", "z", "undo", "Undo"),
                ("ctrl", "s", "save", "Saved"), ("ctrl", "a", "select all", "Selected all"),
                ("ctrl", "f", "find", "Opening find"), ("ctrl", "w", "close", "Closing"),
                ("ctrl", "t", "new tab", "New tab"), ("alt", "f4", "close window", "Closing window"),
                ("alt", "tab", "switch", "Switching windows"),
                ("win", "d", "desktop", "Showing desktop"),
                ("win", "e", "explorer", "Opening Explorer"),
                ("win", "l", "lock", "Locking"),
            ]
            for mod, key, keyword, msg in shortcuts:
                if keyword in text and mod in text:
                    safe_hotkey(mod, key)
                    if self.tts:
                        self.tts.speak(msg)
                    return {"success": True, "message": f"{mod}+{key}", "action": "shortcut"}

        except Exception as e:
            self.logger.error(f"Keyboard error: {e}")
        return {"success": False, "message": "Unknown keyboard command", "action": "keyboard_control"}

    def _press_key(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        """Handle explicit key press from LLM."""
        key_combo = params.get("key_combo", "")
        if key_combo:
            if "+" in key_combo:
                import pyautogui
                pyautogui.hotkey(*key_combo.split('+'))
            else:
                safe_press(key_combo)
            return {"success": True, "message": f"Pressed {key_combo}", "action": "key_press"}
        return {"success": False, "message": "No key specified", "action": "press_key"}

    # ── Mouse Control ─────────────────────────────────────────────────

    def _mouse_control(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        import pyautogui
        text = raw_text.lower()

        try:
            button = params.get("button", "left")
            x = params.get("x")
            y = params.get("y")

            if "right click" in text:
                pyautogui.rightClick()
                return {"success": True, "message": "Right clicked", "action": "mouse_right_click"}
            elif "double click" in text:
                pyautogui.doubleClick()
                return {"success": True, "message": "Double clicked", "action": "mouse_double_click"}
            elif "click" in text:
                if x is not None and y is not None:
                    safe_click(int(x), int(y))
                else:
                    safe_click()
                return {"success": True, "message": "Clicked", "action": "mouse_click"}
            elif "move" in text:
                if x is not None and y is not None:
                    safe_move(int(x), int(y), duration=0.5)
                    return {"success": True, "message": f"Moved to {x},{y}", "action": "mouse_move"}
                else:
                    w, h = pyautogui.size()
                    safe_move(w // 2, h // 2, duration=0.5)
                    return {"success": True, "message": "Moved to center", "action": "mouse_move"}
            elif "scroll" in text:
                amount = params.get("amount", 300)
                if "up" in text:
                    safe_scroll(int(amount))
                else:
                    safe_scroll(-int(amount))
                return {"success": True, "message": "Scrolled", "action": "mouse_scroll"}
            elif "position" in text or "where" in text:
                px, py = pyautogui.position()
                if self.tts:
                    self.tts.speak(f"Mouse is at {px}, {py}")
                return {"success": True, "message": f"Position: {px}, {py}", "action": "mouse_position"}

        except Exception as e:
            self.logger.error(f"Mouse error: {e}")
        return {"success": False, "message": "Mouse control failed", "action": "mouse_control"}

    # ── Typing ────────────────────────────────────────────────────────

    def _type_text(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        text_to_type = params.get("text", "")
        if not text_to_type:
            for trigger in ["type", "write", "enter"]:
                if trigger in raw_text.lower():
                    text_to_type = raw_text.lower().split(trigger, 1)[1].strip()
                    break

        if text_to_type:
            time.sleep(1)
            safe_type(text_to_type, interval=0.03)
            if self.tts:
                self.tts.speak("Done typing")
            return {"success": True, "message": "Typed text", "action": "type_text"}

        return {"success": False, "message": "No text to type", "action": "type_text"}

    # ── System Info ───────────────────────────────────────────────────

    def _system_info(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        text = raw_text.lower()

        if any(w in text for w in ["time", "clock"]):
            now = datetime.datetime.now().strftime("%I:%M %p")
            msg = f"The time is {now}"
            if self.tts:
                self.tts.speak(msg)
            return {"success": True, "message": msg, "action": "time_query"}
        elif any(w in text for w in ["date", "today", "day"]):
            today = datetime.date.today().strftime("%B %d, %Y")
            day_name = datetime.date.today().strftime("%A")
            msg = f"Today is {day_name}, {today}"
            if self.tts:
                self.tts.speak(msg)
            return {"success": True, "message": msg, "action": "date_query"}

        # General system info
        import psutil
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        msg = f"CPU: {cpu}%, RAM: {ram}%"
        if self.tts:
            self.tts.speak(msg)
        return {"success": True, "message": msg, "action": "system_info"}
