import os
import subprocess
import webbrowser
import logging
import json
import re
from typing import Dict, Any
from modules.automation_workflows import AutomationWorkflows
from modules.screen_analyzer import ScreenAnalyzer
from modules.dictation_engine import DictationEngine
from modules.pyautogui_config import (safe_click, safe_type, safe_press, 
                                      safe_hotkey, safe_move, safe_scroll)
from modules.command_parser import CommandParser
from modules.task_queue import execute_async
from modules.plugin_manager import PluginManager
from modules.task_suggester import TaskSuggester
from modules.clipboard_manager import ClipboardManager
from modules.file_searcher import FileSearcher
from modules.llm_engine import LLMEngine
from modules.utils import DATA_DIR



class AIBrain:
    """
    The Intelligence Center of Nova.
    Interprets user intent and executes corresponding actions.
    Now supports Multitasking and Command Chaining!
    """
    
    def __init__(self, tts_engine, speech_engine=None):
        self.logger = logging.getLogger('AIBrain')
        self.tts = tts_engine
        self.speech = speech_engine
        self.workflows = AutomationWorkflows(tts_engine)
        self.screen_analyzer = ScreenAnalyzer(tts_engine)
        self.dictation = DictationEngine(speech_engine, tts_engine) if speech_engine else None
        self.screen_analyzer = ScreenAnalyzer(tts_engine)
        self.dictation = DictationEngine(speech_engine, tts_engine) if speech_engine else None
        self.plugin_manager = PluginManager(self)
        self.plugin_manager.load_plugins()
        self.task_suggester = TaskSuggester(DATA_DIR)
        self.clipboard_manager = ClipboardManager(DATA_DIR)
        self.file_searcher = FileSearcher()
        self.llm_engine = LLMEngine()
        
        # Memory & Safety
        self.last_command = None
        self.pending_confirmation = None
        
    def parse_and_execute(self, text: str) -> Dict[str, Any]:
        """
        Parse user input and execute command(s).
        Supports chained commands (e.g., "open chrome and play music")
        """
        if not text:
            return {"success": False, "message": "No input provided", "action": "none"}
            
        text = text.lower()
        self.logger.info(f"AI Brain processing: {text}")
        
        # Check for chained commands
        is_chained, commands = CommandParser.parse_command(text)
        
        if is_chained and len(commands) > 1:
            self.logger.info(f"Detected chained commands: {commands}")
            self.tts.speak(f"Executing {len(commands)} tasks")
            
            results = []
            for cmd in commands:
                # Clean up command
                cmd = CommandParser.format_command_for_execution(cmd)
                
                # Execute each command asynchronously
                execute_async(self._process_single_command, cmd)
                results.append({"success": True, "message": f"Queued: {cmd}", "action": "queued"})
            
            return {"success": True, "message": "Multiple tasks started", "action": "multitask"}
            
        # Check for confirmation response
        if self.pending_confirmation:
            if any(word in text for word in ["yes", "sure", "continue", "do it", "confirm"]):
                cmd = self.pending_confirmation
                self.pending_confirmation = None
                self.tts.speak("Confirmed. Executing.")
                return self._process_single_command(cmd, bypass_safety=True)
            elif any(word in text for word in ["no", "cancel", "stop", "don't"]):
                self.pending_confirmation = None
                self.tts.speak("Action cancelled.")
                return {"success": True, "message": "Cancelled", "action": "cancelled"}
            else:
                # If they say something else, assume they ignored the confirmation or are starting a new task
                self.pending_confirmation = None
        
        # Session Memory: "Do that again"
        if any(phrase in text for phrase in ["do that again", "repeat that", "continue from where we stopped"]):
            if self.last_command:
                self.tts.speak("Repeating last command.")
                return self._process_single_command(self.last_command, bypass_safety=True)
            else:
                self.tts.speak("I don't have a previous command to repeat.")
                return {"success": False, "message": "No memory", "action": "memory_error"}

        # Try LLM Engine first if available
        if self.llm_engine.provider:
            self.logger.info("Delegating to LLM Engine...")
            try:
                llm_decision = self.llm_engine.decide_action(text, context=f"Last command: {self.last_command}")
                self.logger.info(f"LLM Decision: {llm_decision}")
                
                if llm_decision.get("action") != "error":
                    return self._execute_llm_action(llm_decision)
                else:
                    self.logger.warning("LLM returned error, falling back to legacy parser.")
            except Exception as e:
                self.logger.error(f"LLM Execution failed: {e}. Falling back to legacy parser.")

        # Single command execution (Fallback or if LLM unavailable)
        return self._process_single_command(text)

    def _execute_llm_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the action decided by the LLM"""
        action = action_data.get("action")
        params = action_data.get("parameters", {})
        response = action_data.get("response")
        thought = action_data.get("thought")
        
        self.logger.info(f"Executing LLM Action: {action} | Thought: {thought}")
        
        if response and action != "conversation":
            # Speak the response unless it's just a conversation response which is handled below
            self.tts.speak(response)
            
        if action == "conversation":
            if response:
                self.tts.speak(response)
            return {"success": True, "message": response, "action": "conversation"}
            
        elif action == "open_app":
            app = params.get("parsed_name", "")
            return self._handle_open_command(f"open {app}")
            
        elif action == "close_app":
            app = params.get("parsed_name", "")
            return self._handle_close_command(f"close {app}")
            
        elif action == "web_search":
            query = params.get("query", "")
            return self._handle_search_command(f"search {query}")
            
        elif action == "navigate":
            url = params.get("url", "")
            return self._handle_navigation_command(f"go to {url}")
            
        elif action == "type_text":
            text = params.get("text", "")
            return self._handle_typing_command(f"type {text}")
            
        elif action == "mouse_click":
            # Direct implementation for better control
            import pyautogui
            button = params.get("button", "left")
            clicks = 2 if params.get("double") else 1
            pyautogui.click(button=button, clicks=clicks)
            return {"success": True, "message": "Clicked", "action": "mouse_click"}
            
        elif action == "mouse_move":
            x = params.get("x")
            y = params.get("y")
            if x is not None and y is not None:
                safe_move(int(x), int(y))
                return {"success": True, "message": f"Moved to {x},{y}", "action": "mouse_move"}
                
        elif action == "mouse_scroll":
            amount = params.get("amount", 100)
            direction = params.get("direction", "down")
            if direction == "up":
                safe_scroll(int(amount))
            else:
                safe_scroll(-int(amount))
            return {"success": True, "message": "Scrolled", "action": "mouse_scroll"}
            
        elif action == "press_key":
            keys = params.get("key_combo", "")
            # Handle combo like "ctrl+s"
            if "+" in keys:
                import pyautogui
                pyautogui.hotkey(*keys.split('+'))
            else:
                safe_press(keys)
            return {"success": True, "message": f"Pressed {keys}", "action": "key_press"}
            
        elif action == "system_command":
            cmd = params.get("command", "")
            if cmd in ["shutdown", "restart", "sleep", "lock"]:
                return self._handle_system_command(cmd)
            elif cmd in ["volume_up", "volume_down", "mute"]:
                 # Map to media control
                 return self._handle_media_control(cmd)

        elif action == "run_shell":
            cmd = params.get("command", "")
            return self._handle_raw_command(f"execute {cmd}")

                 
        elif action == "analyze_screen":
            prompt = params.get("prompt", "Describe this screen")
            return self._handle_screen_analysis(f"analyze screen {prompt}") # Helper handles format?
            # Wait, _handle_screen_analysis expects command text but calls screen analyzer.
            # Let's check _handle_screen_analysis later or just call screen_analyzer directly.
            # For now, simplistic fallback:
            # But wait, ScreenAnalyzer uses OpenAI too.
            # If LLM triggered this, it means user wants vision.
            # Let's trust existing handler for now or wire it up.
            # Actually, let's call existing handler to be safe.
            return self._handle_screen_analysis(f"analyze screen {prompt}")

        elif action == "find_files":
            query = params.get("query", "")
            return self._handle_file_search(query)
            
        elif action == "play_media":
            query = params.get("query", "")
            return self._handle_youtube(f"play {query}")
            
        elif action == "set_reminder":
            text = params.get("text", "")
            time = params.get("time", "")
            return self._handle_reminder(f"remind me to {text} at {time}")

        elif action == "vibe_code":
            prompt = params.get("prompt", "")
            self.tts.speak("Activating Vibe Coding Mode. Analyzing request...")
            # Delegate to ProjectPlugin
            plugin = self.plugin_manager.plugins.get('project_plugin')
            if plugin:
                return plugin.vibe_coding(prompt)
            else:
                return {"success": False, "message": "Result: Project plugin not loaded", "action": "error"}

        elif action == "multitask":

            actions = params.get("actions", [])
            results = []
            for sub_action in actions:
                res = self._execute_llm_action(sub_action)
                results.append(res)
            return {"success": True, "message": "Executed multiple actions", "action": "multitask", "details": results}

        # Fallback
        self.logger.warning(f"LLM suggested unknown action: {action}")
        return self._process_single_command(text)


    def _process_single_command(self, text: str, bypass_safety: bool = False) -> Dict[str, Any]:
        """Process a single command"""
        
        # SAFETY LAYER (Feature 1)
        dangerous_keywords = ["uninstall", "delete", "remove", "format", "wipe"]
        if not bypass_safety and any(keyword in text for keyword in dangerous_keywords):
            # Exclude simple things like "delete file" if we want to be annoying, 
            # but for "uninstall python" we definitely want a check.
            # Let's be safe for now.
            self.pending_confirmation = text
            msg = f"You are trying to {text}. This might be dangerous. Should I continue?"
            self.tts.speak(msg)
            return {"success": True, "message": "Waiting for confirmation", "action": "safety_check"}

        # Update Memory
        self.last_command = text

        # PLUGINS (Feature 7)
        # Check if any plugin can handle this intent
        # For now, we pass the raw text to plugins to see if they claim it
        # In a real NLP system, we'd classify intent first.
        # Here we iterate plugins and let them check keywords.
        for name, plugin in self.plugin_manager.plugins.items():
            for intent, handler in plugin.get_intents().items():
                # This is a simplified intent matching. 
                # Plugins should probably expose keywords or regex.
                # For now, we'll assume plugins implement a `can_handle(text)` method or similar
                # But to stick to the base class structure:
                pass 
                
        # Better approach: Let plugins register keywords?
        # Or just check specific plugins we know we added.
        
        # Check loaded plugins for specific capabilities
        # This is a simple integration for now.
        for name, plugin in self.plugin_manager.plugins.items():
            if hasattr(plugin, 'handle_command'):
                result = plugin.handle_command(text)
                if result:
                    return result

        # AUTOMATION WORKFLOWS (Highest Priority)
        # WhatsApp
        if "whatsapp" in text or "send message" in text or "send a message" in text:
            return self._handle_whatsapp(text)
        
        # Email
        if "email" in text or "gmail" in text or "send email" in text:
            return self._handle_email(text)
        if "screenshot" in text or "screen capture" in text or "capture screen" in text:
            return self._handle_screenshot(text)
        
        # Reminder
        if "remind me" in text or "set reminder" in text or "reminder" in text:
            return self._handle_reminder(text)
        
        # YouTube
        if "play" in text and ("youtube" in text or "video" in text or "song" in text or "music" in text):
            return self._handle_youtube(text)
        
        # Note taking
        if "create note" in text or "make note" in text or "take note" in text:
            return self._handle_note(text)
        
        # SCREEN ANALYSIS (New Feature)
        # Support both American (analyze) and British (analyse) spelling
        screen_keywords = [
            "analyze screen", "analyse screen", 
            "what's on screen", "what do you see",
            "check screen", "look at screen",
            "summarize screen", "summarise screen",
            "describe screen", "read screen",
            "summarise the screen", "summarize the screen",
            "analyze the screen", "analyse the screen"
        ]
        
        if any(phrase in text for phrase in screen_keywords):
            return self._handle_screen_analysis(text)
            
        if "read screen" in text or "read my screen" in text or "what does it say" in text:
            return self._handle_read_screen(text)
        
        if "describe screen" in text or "describe what you see" in text:
            return self._handle_describe_screen(text)
        
        if "find on screen" in text or "locate on screen" in text:
            return self._handle_find_on_screen(text)
        
        # DICTATION MODE (New Feature)
        if "start dictation" in text or "begin dictation" in text or "dictation mode" in text:
            return self._handle_start_dictation(text)
        
        if "stop dictation" in text or "end dictation" in text or "exit dictation" in text:
            return self._handle_stop_dictation(text)
        
        # Voice typing (one-time)
        if "voice type" in text or "type with voice" in text:
            return self._handle_voice_type(text)
        
        # Window management
        if any(phrase in text for phrase in ["minimize all", "minimise all", "show desktop", "minimize screen", "minimise screen", "minimise the screen"]):
            return self.workflows.minimize_all_windows()
        
        if any(phrase in text for phrase in ["maximize", "maximise"]) and any(word in text for word in ["window", "screen"]):
            return self.workflows.maximize_window()
            
        if any(phrase in text for phrase in ["close window", "close this"]):
            return self.workflows.close_current_window()
        
        # HIGH PRIORITY: Time and Date queries
        if any(word in text for word in ["time", "clock", "what time"]):
            return self._handle_time_query(text)
        
        if any(word in text for word in ["date", "today", "what day", "what's the date"]):
            return self._handle_date_query(text)
        
        # Weather queries
        if any(word in text for word in ["weather", "temperature", "forecast"]):
            return self._handle_weather_query(text)
        
        # Pattern 1: Open/Launch/Start applications
        if any(word in text for word in ["open", "launch", "start", "run"]):
            return self._handle_open_command(text)
        
        # Pattern 2: Close/Kill applications
        elif any(word in text for word in ["close", "kill", "stop", "exit"]):
            return self._handle_close_command(text)
        
        # Pattern 3: Search/Google/Find
        elif any(word in text for word in ["search", "google", "find", "look up"]):
            return self._handle_search_command(text)
        
        # Pattern 4: Mouse control
        elif any(word in text for word in ["click", "mouse", "move mouse", "scroll", "right click", "double click"]):
            return self._handle_mouse_control(text)
        
        # Pattern 5: Keyboard control
        elif any(word in text for word in ["press", "hold", "release", "key", "shortcut", "ctrl", "alt", "shift"]):
            return self._handle_keyboard_control(text)
        
        # Pattern 6: Navigate to URL
        elif any(word in text for word in ["go to", "navigate", "visit", "browse"]):
            return self._handle_navigation_command(text)
        
        # Pattern 7: File operations
        elif any(word in text for word in ["create", "delete", "move", "copy", "rename"]):
            return self._handle_file_operation(text)
        
        # Pattern 8: System commands
        elif any(word in text for word in ["shutdown", "restart", "sleep", "lock"]):
            return self._handle_system_command(text)
        
        # Pattern 9: Volume/Brightness control
        elif any(word in text for word in ["volume", "brightness", "mute", "unmute"]):
            return self._handle_media_control(text)
        
        # Pattern 10: Type/Write text
        elif any(word in text for word in ["type", "write", "enter"]):
            return self._handle_typing_command(text)
        
        # Pattern 11: Execute PowerShell/CMD commands
        elif "execute" in text or "command" in text or "powershell" in text:
            return self._handle_raw_command(text)
            
        # Pattern 12: Jokes
        elif "joke" in text:
            return self._handle_joke(text)
            
        # Pattern 13: Task Suggestions (New Feature)
        elif any(phrase in text for phrase in ["what should i do", "suggest", "give me a task", "what do you suggest", "what next", "any ideas"]):
            return self._handle_task_suggestion(text)

        # Pattern 15: Clipboard & Snippets (New Feature)
        elif "snippet" in text or ("save" in text and ("text" in text or "this" in text)):
             return self._handle_clipboard(text)
             
        # Pattern 16: Automation Templates (New Feature)
        elif "automate" in text or "run template" in text or "start routine" in text:
            return self._handle_automation_template(text)

        # Pattern 17: Natural Language File Search (New Feature)
        # Broader matching: "find file", "search for document", "open file about X"
        elif ("file" in text or "document" in text) and ("find" in text or "search" in text or "open" in text or "look for" in text):
            return self._handle_file_search(text)

        # Pattern 18: Dashboard (New Feature)
        elif "dashboard" in text or "hud" in text or "panel" in text:
            return self._handle_dashboard(text)

        # Pattern 14: Math/Calculator
        elif any(op in text for op in ["+", "-", "*", "/", "plus", "minus", "times", "divided", "calculate", "what is", "what's", "x"]):
            # Check if it looks like math (has numbers)
            if any(char.isdigit() for char in text):
                return self._handle_math(text)
            else:
                return self._smart_app_launch(text)
                
        # Pattern 14: Conversational (Greetings/Goodbyes)
        elif any(word in text for word in ["hello", "hi", "hey", "good morning", "good evening"]):
            return {"success": True, "message": "Hello! How can I help?", "action": "greeting"}
            
        elif any(word in text for word in ["bye", "goodbye", "good night", "exit", "quit"]):
            return {"success": True, "message": "Goodbye! Shutting down.", "action": "goodbye"}
            
        elif any(word in text for word in ["thanks", "thank you"]):
            return {"success": True, "message": "You're welcome!", "action": "thanks"}
        
        # Default: Try to interpret as application name
        else:
            return self._smart_app_launch(text)

    def _handle_math(self, text: str) -> Dict[str, Any]:
        """Handle math calculations"""
        try:
            # Clean up text to get just the expression
            expr = text.replace("what is", "").replace("calculate", "").replace("solve", "")
            expr = expr.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/")
            expr = expr.replace("x", "*") # Common multiplication symbol
            
            # Remove non-math characters (keep numbers, operators, dots, parentheses)
            clean_expr = "".join(c for c in expr if c.isdigit() or c in "+-*/.()")
            
            if not clean_expr:
                return self._smart_app_launch(text)
                
            # Evaluate safely
            # pylint: disable=eval-used
            result = eval(clean_expr)
            
            # Format result
            if isinstance(result, float) and result.is_integer():
                result = int(result)
                
            response = f"The answer is {result}"
            self.tts.speak(response)
            return {"success": True, "message": response, "action": "math"}
            
        except Exception as e:
            self.logger.error(f"Math error: {e}")
            # If math fails, fall back to smart launch (might be an app name with numbers)
            return self._smart_app_launch(text)

    def _handle_joke(self, text: str) -> Dict[str, Any]:
        """Tell a joke"""
        import random
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs.",
            "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
            "I would tell you a UDP joke, but you might not get it.",
            "Why did the Python programmer break up with Java? Because they treated him like an object.",
            "What is a computer's favorite snack? Microchips.",
            "Why was the computer cold? It left its Windows open.",
            "Why did the developer go broke? Because he used up all his cache.",
            "A SQL query walks into a bar, walks up to two tables and asks, 'Can I join you?'"
        ]
        joke = random.choice(jokes)
        self.tts.speak(joke)
        return {"success": True, "message": "Told a joke", "action": "joke"}

    def _handle_task_suggestion(self, text: str) -> Dict[str, Any]:
        """Handle task suggestions"""
        suggestion = self.task_suggester.get_suggestion()
        self.tts.speak(suggestion)
        return {"success": True, "message": suggestion, "action": "suggest_task"}

    def _handle_clipboard(self, text: str) -> Dict[str, Any]:
        """Handle clipboard snippet saving and retrieval"""
        if "save" in text or "remember" in text:
            # Try to infer description
            description = "general"
            if " as " in text:
                description = text.split(" as ", 1)[1].strip()
            elif " about " in text:
                description = text.split(" about ", 1)[1].strip()
            elif " named " in text:
                description = text.split(" named ", 1)[1].strip()
            
            result = self.clipboard_manager.save_snippet(description)
            self.tts.speak(result)
            return {"success": True, "message": result, "action": "save_snippet"}
            
        elif "show" in text or "find" in text or "read" in text or "get" in text or "list" in text:
            query = "all snippets"
            # Extract query "show snippets about python" -> "python"
            if " about " in text:
                query = text.split(" about ", 1)[1].strip()
            elif " for " in text:
                query = text.split(" for ", 1)[1].strip()
            
            snippets = self.clipboard_manager.find_snippets(query)
            
            if not snippets:
                msg = f"No snippets found for {query}"
                self.tts.speak(msg)
                return {"success": False, "message": msg, "action": "find_snippet"}
            
            # Speak count
            self.tts.speak(f"Found {len(snippets)} snippets.")
            
            # Format message
            msg = "Here are your snippets:\n"
            for s in snippets:
                msg += f"- [{s['description']}] {s['preview']}\n"
                
            return {"success": True, "message": msg, "action": "show_snippets"}
            
        return {"success": False, "message": "Unknown clipboard command", "action": "unknown"}

    def _handle_automation_template(self, text: str) -> Dict[str, Any]:
        """Handle automation templates"""
        # Extract template name
        # "automate my weekly report" -> "weekly report"
        template_name = text
        for trigger in ["automate", "run template", "start routine", "run"]:
            if trigger in text:
                parts = text.split(trigger, 1)
                if len(parts) > 1:
                    template_name = parts[1].strip()
                    break
        
        # Clean up "my"
        template_name = template_name.replace("my ", "").strip()
        
        return self.workflows.run_automation_template(template_name)

    def _handle_file_search(self, text: str) -> Dict[str, Any]:
        """Handle natural language file search"""
        self.tts.speak("Searching for files...")
        results = self.file_searcher.search(text)
        
        if not results:
            self.tts.speak("I couldn't find any matching files.")
            return {"success": False, "message": "No files found", "action": "file_search_empty"}
        
        top_match = results[0]
        # If confidence is good (using score logic implicit in ordering), open it
        
        # If user said "open", open the first one
        if "open" in text:
            self.tts.speak(f"Opening {top_match['name']}")
            try:
                os.startfile(top_match['path'])
                return {"success": True, "message": f"Opened {top_match['name']}", "action": "open_file"}
            except Exception as e:
                self.logger.error(f"Failed to open file: {e}")
                return {"success": False, "message": str(e), "action": "open_file_error"}
        else:
            # Just list them
            msg = "Found these files:\n"
            for r in results[:3]:
                msg += f"- {r['name']} ({r['score']})\n"
            self.tts.speak(f"I found {len(results)} files. The best match is {top_match['name']}")
            return {"success": True, "message": msg, "action": "file_search_list"}

    def _handle_dashboard(self, text: str) -> Dict[str, Any]:
        """Handle dashboard commands"""
        if "close" in text or "hide" in text:
            self.tts.speak("Hiding dashboard")
            return {"success": True, "message": "Dashboard hidden", "action": "close_dashboard"}
        else:
            self.tts.speak("Opening dashboard")
            return {"success": True, "message": "Dashboard opened", "action": "open_dashboard"}

    def _handle_open_command(self, text: str) -> Dict[str, Any]:
        """Handle open/launch/start commands - Universal Version"""
        # Extract app name
        for trigger in ["open", "launch", "start", "run"]:
            if trigger in text:
                app_name = text.split(trigger, 1)[1].strip()
                break
        
        self.tts.speak(f"Opening {app_name}")
        
        # Method 1: Common applications mapping (Fastest)
        app_map = {
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "paint": "mspaint.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
            "task manager": "taskmgr.exe",
            "control panel": "control.exe",
            "settings": "ms-settings:",
        }
        
        # If it's a known system app, run it directly
        if app_name.lower() in app_map:
            try:
                executable = app_map[app_name.lower()]
                if executable.startswith("ms-"):
                    subprocess.Popen(["start", executable], shell=True)
                else:
                    subprocess.Popen([executable], shell=True)
                return {"success": True, "message": f"Opened {app_name}", "action": "open_app"}
            except:
                pass # Fallback to Method 2
        
        # Method 2: Universal Windows Search (Opens ANYTHING)
        try:
            self.logger.info(f"Using Windows Search to open: {app_name}")
            
            # 1. Press Windows Key
            safe_press('win')
            import time
            time.sleep(0.5) # Wait for menu
            
            # 2. Type the app name
            safe_type(app_name, interval=0.01)
            time.sleep(0.8) # Wait for search results
            
            # 3. Press Enter to open best match
            safe_press('enter')
            
            return {"success": True, "message": f"Opened {app_name}", "action": "open_app_universal"}
            
        except Exception as e:
            self.logger.error(f"Failed to open {app_name}: {e}")
            self.tts.speak(f"Sorry, I couldn't find {app_name}")
            return {"success": False, "message": str(e), "action": "open_app_error"}

    def _handle_close_command(self, text: str) -> Dict[str, Any]:
        """Handle close/kill commands"""
        for trigger in ["close", "kill", "stop", "exit"]:
            if trigger in text:
                app_name = text.split(trigger, 1)[1].strip()
                break
        
        # Map to process names
        process_map = {
            "chrome": "chrome.exe",
            "notepad": "notepad.exe",
            "calculator": "calculator.exe",
            "calc": "calculator.exe",
        }
        
        process_name = process_map.get(app_name, app_name + ".exe")
        
        try:
            subprocess.run(["taskkill", "/F", "/IM", process_name], check=True, capture_output=True)
            self.tts.speak(f"Closed {app_name}")
            return {"success": True, "message": f"Closed {app_name}", "action": "close_app"}
        except Exception as e:
            self.logger.error(f"Failed to close {app_name}: {e}")
            self.tts.speak(f"Couldn't close {app_name}")
            return {"success": False, "message": str(e), "action": "close_app"}
    
    def _handle_search_command(self, text: str) -> Dict[str, Any]:
        """Handle search commands"""
        # Extract query
        for trigger in ["search for", "google", "search", "find", "look up"]:
            if trigger in text:
                query = text.split(trigger, 1)[1].strip()
                break
        
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        self.tts.speak(f"Searching for {query}")
        return {"success": True, "message": f"Searching for {query}", "action": "search"}
    
    def _handle_navigation_command(self, text: str) -> Dict[str, Any]:
        """Handle URL navigation"""
        for trigger in ["go to", "navigate to", "visit", "browse to"]:
            if trigger in text:
                url = text.split(trigger, 1)[1].strip()
                break
        
        # Add protocol if missing
        if not url.startswith("http"):
            url = "https://" + url
        
        webbrowser.open(url)
        self.tts.speak(f"Opening {url}")
        return {"success": True, "message": f"Navigating to {url}", "action": "navigate"}
    
    def _handle_file_operation(self, text: str) -> Dict[str, Any]:
        """Handle file operations"""
        self.tts.speak("File operations require specific paths. Please provide more details.")
        return {"success": False, "message": "Need more details", "action": "file_op"}
    
    def _handle_system_command(self, text: str) -> Dict[str, Any]:
        """Handle system commands like shutdown, restart"""
        if "shutdown" in text:
            self.tts.speak("Shutting down the system")
            subprocess.run(["shutdown", "/s", "/t", "10"])
            return {"success": True, "message": "Shutting down", "action": "shutdown"}
        elif "restart" in text:
            self.tts.speak("Restarting the system")
            subprocess.run(["shutdown", "/r", "/t", "10"])
            return {"success": True, "message": "Restarting", "action": "restart"}
        elif "sleep" in text:
            self.tts.speak("Putting system to sleep")
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return {"success": True, "message": "Sleep mode", "action": "sleep"}
        elif "lock" in text:
            self.tts.speak("Locking the system")
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            return {"success": True, "message": "Locked", "action": "lock"}
        
        return {"success": False, "message": "Unknown system command", "action": "system"}
    
    def _handle_media_control(self, text: str) -> Dict[str, Any]:
        """Handle volume and brightness"""
        try:
            if "mute" in text:
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                from comtypes import CLSCTX_ALL
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = interface.QueryInterface(IAudioEndpointVolume)
                volume.SetMute(1, None)
                self.tts.speak("Muted")
                return {"success": True, "message": "Muted", "action": "mute"}
            elif "unmute" in text:
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                from comtypes import CLSCTX_ALL
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = interface.QueryInterface(IAudioEndpointVolume)
                volume.SetMute(0, None)
                self.tts.speak("Unmuted")
                return {"success": True, "message": "Unmuted", "action": "unmute"}
        except Exception as e:
            self.logger.error(f"Media control error: {e}")
        
        return {"success": False, "message": "Media control not available", "action": "media"}
    
    def _handle_typing_command(self, text: str) -> Dict[str, Any]:
        """Handle typing text"""
        import time
        
        for trigger in ["type", "write", "enter"]:
            if trigger in text:
                content = text.split(trigger, 1)[1].strip()
                break
        
        time.sleep(2)  # Give user time to focus window
        safe_type(content, interval=0.03)  # Use safe typing with reliable delay
        self.tts.speak("Done typing")
        return {"success": True, "message": "Typed text", "action": "type"}
    
    def _handle_raw_command(self, text: str) -> Dict[str, Any]:
        """Execute raw PowerShell commands"""
        self.tts.speak("Executing command")
        # Extract command after "execute" or similar
        for trigger in ["execute", "run command", "powershell"]:
            if trigger in text:
                cmd = text.split(trigger, 1)[1].strip()
                break
        
        try:
            result = subprocess.run(["powershell", "-Command", cmd], 
                                  capture_output=True, text=True, timeout=10)
            self.tts.speak("Command executed")
            return {"success": True, "message": result.stdout, "action": "raw_command"}
        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            return {"success": False, "message": str(e), "action": "raw_command"}
    
    def _smart_app_launch(self, text: str) -> Dict[str, Any]:
        """Try to intelligently launch an app from just the name"""
        # Remove common words
        text = text.replace("please", "").replace("can you", "").strip()
        
        # Safety check: If text is too long or has many words, it's probably not an app
        if len(text.split()) > 2:
            self.logger.warning(f"Ignoring unknown long command: {text}")
            return {"success": False, "message": "Unknown command", "action": "unknown"}
            
        # Try as executable
        try:
            # Only try if it looks like a valid app name (alphanumeric)
            if text.replace(" ", "").isalnum():
                subprocess.Popen([text + ".exe"], shell=True)
                self.tts.speak(f"Launching {text}")
                return {"success": True, "message": f"Launched {text}", "action": "smart_launch"}
            else:
                return {"success": False, "message": "Invalid app name", "action": "unknown"}
        except:
            self.tts.speak("I'm not sure how to do that")
            return {"success": False, "message": "Unknown command", "action": "unknown"}
    
    def _handle_time_query(self, text: str) -> Dict[str, Any]:
        """Handle time queries"""
        import datetime
        now = datetime.datetime.now().strftime("%I:%M %p")
        self.tts.speak(f"The time is {now}")
        return {"success": True, "message": f"The time is {now}", "action": "time_query"}
    
    def _handle_date_query(self, text: str) -> Dict[str, Any]:
        """Handle date queries"""
        import datetime
        today = datetime.date.today().strftime("%B %d, %Y")
        day_name = datetime.date.today().strftime("%A")
        self.tts.speak(f"Today is {day_name}, {today}")
        return {"success": True, "message": f"Today is {day_name}, {today}", "action": "date_query"}
    
    def _handle_weather_query(self, text: str) -> Dict[str, Any]:
        """Handle weather queries"""
        # Extract city if mentioned
        city = "your location"
        if " in " in text:
            city = text.split(" in ")[1].strip()
        
        self.tts.speak(f"To get weather information, please add your API key to the config file")
        return {"success": False, "message": "Weather API key required", "action": "weather_query"}
    
    def _handle_mouse_control(self, text: str) -> Dict[str, Any]:
        """Handle mouse control commands"""
        import pyautogui
        import time
        
        try:
            # Click commands
            if "click" in text:
                if "right click" in text:
                    pyautogui.rightClick()
                    self.tts.speak("Right clicked")
                    return {"success": True, "message": "Right clicked", "action": "mouse_right_click"}
                elif "double click" in text:
                    pyautogui.doubleClick()
                    self.tts.speak("Double clicked")
                    return {"success": True, "message": "Double clicked", "action": "mouse_double_click"}
                else:
                    safe_click()
                    self.tts.speak("Clicked")
                    return {"success": True, "message": "Clicked", "action": "mouse_click"}
            
            # Move mouse
            elif "move mouse" in text or "move cursor" in text:
                # Extract coordinates if provided
                words = text.split()
                if "to" in words:
                    try:
                        idx = words.index("to")
                        x = int(words[idx + 1])
                        y = int(words[idx + 2])
                        safe_move(x, y, duration=0.5)
                        self.tts.speak(f"Moved mouse to {x}, {y}")
                        return {"success": True, "message": f"Moved to {x}, {y}", "action": "mouse_move"}
                    except:
                        pass
                
                # Move to center as default
                screen_width, screen_height = pyautogui.size()
                safe_move(screen_width // 2, screen_height // 2, duration=0.5)
                self.tts.speak("Moved mouse to center")
                return {"success": True, "message": "Moved to center", "action": "mouse_move"}
            
            # Scroll
            elif "scroll" in text:
                if "up" in text:
                    safe_scroll(300)
                    self.tts.speak("Scrolled up")
                    return {"success": True, "message": "Scrolled up", "action": "mouse_scroll"}
                elif "down" in text:
                    safe_scroll(-300)
                    self.tts.speak("Scrolled down")
                    return {"success": True, "message": "Scrolled down", "action": "mouse_scroll"}
                else:
                    safe_scroll(100)
                    self.tts.speak("Scrolled")
                    return {"success": True, "message": "Scrolled", "action": "mouse_scroll"}
            
            # Get mouse position
            elif "position" in text or "where" in text:
                x, y = pyautogui.position()
                self.tts.speak(f"Mouse is at {x}, {y}")
                return {"success": True, "message": f"Position: {x}, {y}", "action": "mouse_position"}
            
        except Exception as e:
            self.logger.error(f"Mouse control error: {e}")
            self.tts.speak("Mouse control failed")
            return {"success": False, "message": str(e), "action": "mouse_error"}
        
        return {"success": False, "message": "Unknown mouse command", "action": "mouse_unknown"}
    
    def _handle_keyboard_control(self, text: str) -> Dict[str, Any]:
        """Handle keyboard control commands"""
        import pyautogui
        import time
        
        try:
            # Press key combinations
            if "press" in text:
                # Common shortcuts
                if "enter" in text or "return" in text:
                    safe_press('enter')
                    self.tts.speak("Pressed Enter")
                    return {"success": True, "message": "Pressed Enter", "action": "key_press"}
                
                elif "escape" in text or "esc" in text:
                    safe_press('esc')
                    self.tts.speak("Pressed Escape")
                    return {"success": True, "message": "Pressed Escape", "action": "key_press"}
                
                elif "space" in text or "spacebar" in text:
                    safe_press('space')
                    self.tts.speak("Pressed Space")
                    return {"success": True, "message": "Pressed Space", "action": "key_press"}
                
                elif "tab" in text:
                    safe_press('tab')
                    self.tts.speak("Pressed Tab")
                    return {"success": True, "message": "Pressed Tab", "action": "key_press"}
                
                elif "backspace" in text:
                    safe_press('backspace')
                    self.tts.speak("Pressed Backspace")
                    return {"success": True, "message": "Pressed Backspace", "action": "key_press"}
                
                elif "delete" in text:
                    safe_press('delete')
                    self.tts.speak("Pressed Delete")
                    return {"success": True, "message": "Pressed Delete", "action": "key_press"}
                
                # Arrow keys
                elif "up arrow" in text or "arrow up" in text:
                    safe_press('up')
                    self.tts.speak("Pressed Up Arrow")
                    return {"success": True, "message": "Pressed Up", "action": "key_press"}
                
                elif "down arrow" in text or "arrow down" in text:
                    safe_press('down')
                    self.tts.speak("Pressed Down Arrow")
                    return {"success": True, "message": "Pressed Down", "action": "key_press"}
                
                elif "left arrow" in text or "arrow left" in text:
                    safe_press('left')
                    self.tts.speak("Pressed Left Arrow")
                    return {"success": True, "message": "Pressed Left", "action": "key_press"}
                
                elif "right arrow" in text or "arrow right" in text:
                    safe_press('right')
                    self.tts.speak("Pressed Right Arrow")
                    return {"success": True, "message": "Pressed Right", "action": "key_press"}
            
            # Keyboard shortcuts
            if "ctrl" in text or "control" in text:
                if "c" in text or "copy" in text:
                    safe_hotkey('ctrl', 'c')
                    self.tts.speak("Copied")
                    return {"success": True, "message": "Ctrl+C", "action": "shortcut"}
                
                elif "v" in text or "paste" in text:
                    safe_hotkey('ctrl', 'v')
                    self.tts.speak("Pasted")
                    return {"success": True, "message": "Ctrl+V", "action": "shortcut"}
                
                elif "x" in text or "cut" in text:
                    safe_hotkey('ctrl', 'x')
                    self.tts.speak("Cut")
                    return {"success": True, "message": "Ctrl+X", "action": "shortcut"}
                
                elif "z" in text or "undo" in text:
                    safe_hotkey('ctrl', 'z')
                    self.tts.speak("Undo")
                    return {"success": True, "message": "Ctrl+Z", "action": "shortcut"}
                
                elif "y" in text or "redo" in text:
                    safe_hotkey('ctrl', 'y')
                    self.tts.speak("Redo")
                    return {"success": True, "message": "Ctrl+Y", "action": "shortcut"}
                
                elif "a" in text or "select all" in text:
                    safe_hotkey('ctrl', 'a')
                    self.tts.speak("Selected all")
                    return {"success": True, "message": "Ctrl+A", "action": "shortcut"}
                
                elif "s" in text or "save" in text:
                    safe_hotkey('ctrl', 's')
                    self.tts.speak("Saved")
                    return {"success": True, "message": "Ctrl+S", "action": "shortcut"}
                
                elif "f" in text or "find" in text:
                    safe_hotkey('ctrl', 'f')
                    self.tts.speak("Opening find")
                    return {"success": True, "message": "Ctrl+F", "action": "shortcut"}
                
                elif "w" in text or "close" in text:
                    safe_hotkey('ctrl', 'w')
                    self.tts.speak("Closing")
                    return {"success": True, "message": "Ctrl+W", "action": "shortcut"}
                
                elif "t" in text or "new tab" in text:
                    safe_hotkey('ctrl', 't')
                    self.tts.speak("New tab")
                    return {"success": True, "message": "Ctrl+T", "action": "shortcut"}
            
            # Alt shortcuts
            if "alt" in text:
                if "f4" in text or "close window" in text:
                    safe_hotkey('alt', 'f4')
                    self.tts.speak("Closing window")
                    return {"success": True, "message": "Alt+F4", "action": "shortcut"}
                
                elif "tab" in text or "switch" in text:
                    safe_hotkey('alt', 'tab')
                    self.tts.speak("Switching windows")
                    return {"success": True, "message": "Alt+Tab", "action": "shortcut"}
            
            # Windows key shortcuts
            if "windows" in text or "win" in text:
                if "d" in text or "desktop" in text:
                    safe_hotkey('win', 'd')
                    self.tts.speak("Showing desktop")
                    return {"success": True, "message": "Win+D", "action": "shortcut"}
                
                elif "e" in text or "explorer" in text:
                    safe_hotkey('win', 'e')
                    self.tts.speak("Opening Explorer")
                    return {"success": True, "message": "Win+E", "action": "shortcut"}
                
                elif "l" in text or "lock" in text:
                    safe_hotkey('win', 'l')
                    self.tts.speak("Locking")
                    return {"success": True, "message": "Win+L", "action": "shortcut"}
                    return {"success": True, "message": "Double clicked", "action": "mouse_double_click"}
                else:
                    safe_click()
                    self.tts.speak("Clicked")
                    return {"success": True, "message": "Clicked", "action": "mouse_click"}
            
            # Move mouse
            elif "move mouse" in text or "move cursor" in text:
                # Extract coordinates if provided
                words = text.split()
                if "to" in words:
                    try:
                        idx = words.index("to")
                        x = int(words[idx + 1])
                        y = int(words[idx + 2])
                        safe_move(x, y, duration=0.5)
                        self.tts.speak(f"Moved mouse to {x}, {y}")
                        return {"success": True, "message": f"Moved to {x}, {y}", "action": "mouse_move"}
                    except:
                        pass
                
                # Move to center as default
                screen_width, screen_height = pyautogui.size()
                safe_move(screen_width // 2, screen_height // 2, duration=0.5)
                self.tts.speak("Moved mouse to center")
                return {"success": True, "message": "Moved to center", "action": "mouse_move"}
            
            # Scroll
            elif "scroll" in text:
                if "up" in text:
                    safe_scroll(300)
                    self.tts.speak("Scrolled up")
                    return {"success": True, "message": "Scrolled up", "action": "mouse_scroll"}
                elif "down" in text:
                    safe_scroll(-300)
                    self.tts.speak("Scrolled down")
                    return {"success": True, "message": "Scrolled down", "action": "mouse_scroll"}
                else:
                    safe_scroll(100)
                    self.tts.speak("Scrolled")
                    return {"success": True, "message": "Scrolled", "action": "mouse_scroll"}
            
            # Get mouse position
            elif "position" in text or "where" in text:
                x, y = pyautogui.position()
                self.tts.speak(f"Mouse is at {x}, {y}")
                return {"success": True, "message": f"Position: {x}, {y}", "action": "mouse_position"}
            
        except Exception as e:
            self.logger.error(f"Mouse control error: {e}")
            self.tts.speak("Mouse control failed")
            return {"success": False, "message": str(e), "action": "mouse_error"}
        
        return {"success": False, "message": "Unknown mouse command", "action": "mouse_unknown"}
    
    def _handle_keyboard_control(self, text: str) -> Dict[str, Any]:
        """Handle keyboard control commands"""
        import pyautogui
        import time
        
        try:
            # Press key combinations
            if "press" in text:
                # Common shortcuts
                if "enter" in text or "return" in text:
                    safe_press('enter')
                    self.tts.speak("Pressed Enter")
                    return {"success": True, "message": "Pressed Enter", "action": "key_press"}
                
                elif "escape" in text or "esc" in text:
                    safe_press('esc')
                    self.tts.speak("Pressed Escape")
                    return {"success": True, "message": "Pressed Escape", "action": "key_press"}
                
                elif "space" in text or "spacebar" in text:
                    safe_press('space')
                    self.tts.speak("Pressed Space")
                    return {"success": True, "message": "Pressed Space", "action": "key_press"}
                
                elif "tab" in text:
                    safe_press('tab')
                    self.tts.speak("Pressed Tab")
                    return {"success": True, "message": "Pressed Tab", "action": "key_press"}
                
                elif "backspace" in text:
                    safe_press('backspace')
                    self.tts.speak("Pressed Backspace")
                    return {"success": True, "message": "Pressed Backspace", "action": "key_press"}
                
                elif "delete" in text:
                    safe_press('delete')
                    self.tts.speak("Pressed Delete")
                    return {"success": True, "message": "Pressed Delete", "action": "key_press"}
                
                # Arrow keys
                elif "up arrow" in text or "arrow up" in text:
                    safe_press('up')
                    self.tts.speak("Pressed Up Arrow")
                    return {"success": True, "message": "Pressed Up", "action": "key_press"}
                
                elif "down arrow" in text or "arrow down" in text:
                    safe_press('down')
                    self.tts.speak("Pressed Down Arrow")
                    return {"success": True, "message": "Pressed Down", "action": "key_press"}
                
                elif "left arrow" in text or "arrow left" in text:
                    safe_press('left')
                    self.tts.speak("Pressed Left Arrow")
                    return {"success": True, "message": "Pressed Left", "action": "key_press"}
                
                elif "right arrow" in text or "arrow right" in text:
                    safe_press('right')
                    self.tts.speak("Pressed Right Arrow")
                    return {"success": True, "message": "Pressed Right", "action": "key_press"}
            
            # Keyboard shortcuts
            if "ctrl" in text or "control" in text:
                if "c" in text or "copy" in text:
                    safe_hotkey('ctrl', 'c')
                    self.tts.speak("Copied")
                    return {"success": True, "message": "Ctrl+C", "action": "shortcut"}
                
                elif "v" in text or "paste" in text:
                    safe_hotkey('ctrl', 'v')
                    self.tts.speak("Pasted")
                    return {"success": True, "message": "Ctrl+V", "action": "shortcut"}
                
                elif "x" in text or "cut" in text:
                    safe_hotkey('ctrl', 'x')
                    self.tts.speak("Cut")
                    return {"success": True, "message": "Ctrl+X", "action": "shortcut"}
                
                elif "z" in text or "undo" in text:
                    safe_hotkey('ctrl', 'z')
                    self.tts.speak("Undo")
                    return {"success": True, "message": "Ctrl+Z", "action": "shortcut"}
                
                elif "y" in text or "redo" in text:
                    safe_hotkey('ctrl', 'y')
                    self.tts.speak("Redo")
                    return {"success": True, "message": "Ctrl+Y", "action": "shortcut"}
                
                elif "a" in text or "select all" in text:
                    safe_hotkey('ctrl', 'a')
                    self.tts.speak("Selected all")
                    return {"success": True, "message": "Ctrl+A", "action": "shortcut"}
                
                elif "s" in text or "save" in text:
                    safe_hotkey('ctrl', 's')
                    self.tts.speak("Saved")
                    return {"success": True, "message": "Ctrl+S", "action": "shortcut"}
                
                elif "f" in text or "find" in text:
                    safe_hotkey('ctrl', 'f')
                    self.tts.speak("Opening find")
                    return {"success": True, "message": "Ctrl+F", "action": "shortcut"}
                
                elif "w" in text or "close" in text:
                    safe_hotkey('ctrl', 'w')
                    self.tts.speak("Closing")
                    return {"success": True, "message": "Ctrl+W", "action": "shortcut"}
                
                elif "t" in text or "new tab" in text:
                    safe_hotkey('ctrl', 't')
                    self.tts.speak("New tab")
                    return {"success": True, "message": "Ctrl+T", "action": "shortcut"}
            
            # Alt shortcuts
            if "alt" in text:
                if "f4" in text or "close window" in text:
                    safe_hotkey('alt', 'f4')
                    self.tts.speak("Closing window")
                    return {"success": True, "message": "Alt+F4", "action": "shortcut"}
                
                elif "tab" in text or "switch" in text:
                    safe_hotkey('alt', 'tab')
                    self.tts.speak("Switching windows")
                    return {"success": True, "message": "Alt+Tab", "action": "shortcut"}
            
            # Windows key shortcuts
            if "windows" in text or "win" in text:
                if "d" in text or "desktop" in text:
                    safe_hotkey('win', 'd')
                    self.tts.speak("Showing desktop")
                    return {"success": True, "message": "Win+D", "action": "shortcut"}
                
                elif "e" in text or "explorer" in text:
                    safe_hotkey('win', 'e')
                    self.tts.speak("Opening Explorer")
                    return {"success": True, "message": "Win+E", "action": "shortcut"}
                
                elif "l" in text or "lock" in text:
                    safe_hotkey('win', 'l')
                    self.tts.speak("Locking")
                    return {"success": True, "message": "Win+L", "action": "shortcut"}
            
        except Exception as e:
            self.logger.error(f"Keyboard control error: {e}")
            self.tts.speak("Keyboard control failed")
            return {"success": False, "message": str(e), "action": "keyboard_error"}
        
        return {"success": False, "message": "Unknown keyboard command", "action": "keyboard_unknown"}
    
    def _handle_whatsapp(self, text: str) -> Dict[str, Any]:
        """Handle WhatsApp message sending"""
        # Extract contact and message
        contact = ""
        message = ""
        
        if "to" in text:
            parts = text.split("to", 1)[1].strip()
            if "saying" in parts:
                contact = parts.split("saying")[0].strip()
                message = parts.split("saying")[1].strip()
            elif "message" in parts:
                # "send a message to Praneeth message hello" - rare but possible
                # But mostly "send a message to Praneeth" -> message defaults or asks
                contact = parts.split("message")[0].strip()
                if "message" in parts: 
                    msg_part = parts.split("message")[1].strip()
                    if msg_part: message = msg_part
            else:
                contact = parts
                message = "Hello" # Default if no message body
        elif "saying" in text:
            # "send message saying hello" (no contact?) - asks or fails
            message = text.split("saying")[1].strip()
        else:
            # Just "send whatsapp message"
            message = "Hello"
        
        return self.workflows.send_whatsapp_message(contact, message)
    
    def _handle_email(self, text: str) -> Dict[str, Any]:
        """Handle email composition"""
        to = ""
        subject = ""
        body = ""
        
        # Extract email components
        if "to" in text:
            to_part = text.split("to")[1].strip()
            if "subject" in to_part:
                to = to_part.split("subject")[0].strip()
                subject_part = to_part.split("subject")[1].strip()
                if "body" in subject_part or "saying" in subject_part:
                    subject = subject_part.split("body")[0] if "body" in subject_part else subject_part.split("saying")[0]
                    body = subject_part.split("body")[1] if "body" in subject_part else subject_part.split("saying")[1]
                else:
                    subject = subject_part
            else:
                to = to_part
        
        return self.workflows.open_gmail_compose(to, subject, body)
    
    def _handle_screenshot(self, text: str) -> Dict[str, Any]:
        """Handle screenshot capture"""
        filename = None
        if "as" in text or "named" in text:
            trigger = "as" if "as" in text else "named"
            filename = text.split(trigger)[1].strip()
        
        return self.workflows.take_screenshot(filename)
    
    def _handle_reminder(self, text: str) -> Dict[str, Any]:
        """Handle reminder setting"""
        import re
        
        # Extract reminder text and time
        reminder_text = text
        minutes = 5  # default
        
        # Look for time mentions
        time_patterns = [
            (r'in (\d+) minutes?', 1),
            (r'in (\d+) hours?', 60),
            (r'after (\d+) minutes?', 1),
            (r'after (\d+) hours?', 60),
        ]
        
        for pattern, multiplier in time_patterns:
            match = re.search(pattern, text)
            if match:
                minutes = int(match.group(1)) * multiplier
                # Remove time part from reminder text
                reminder_text = re.sub(pattern, '', text).strip()
                break
        
        # Clean up reminder text
        reminder_text = reminder_text.replace("remind me", "").replace("to", "").replace("that", "").strip()
        
        return self.workflows.set_reminder(reminder_text, minutes)
    
    def _handle_youtube(self, text: str) -> Dict[str, Any]:
        """Handle YouTube video playback"""
        # Extract search query
        query = text
        for trigger in ["play", "youtube", "video", "song", "music"]:
            query = query.replace(trigger, "")
        query = query.strip()
        
        if not query:
            query = "music"
        
        return self.workflows.play_youtube_video(query)
    
    def _handle_note(self, text: str) -> Dict[str, Any]:
        """Handle note creation"""
        # Extract note content
        note_text = text
        for trigger in ["create note", "make note", "take note", "saying", "that says"]:
            if trigger in note_text:
                note_text = note_text.split(trigger)[1].strip()
                break
        
        return self.workflows.create_note(note_text)
    
    # ==================== SCREEN ANALYSIS HANDLERS ====================
    
    def _handle_screen_analysis(self, text: str) -> Dict[str, Any]:
        """Handle general screen analysis"""
        # Extract custom prompt if provided
        prompt = "What do you see on this screen?"
        if "analyze screen" in text:
            custom = text.split("analyze screen", 1)[1].strip()
            if custom:
                prompt = custom
        
        return self.screen_analyzer.analyze_screen(prompt)
    
    def _handle_read_screen(self, text: str) -> Dict[str, Any]:
        """Handle reading text from screen"""
        return self.screen_analyzer.read_screen_text()
    
    def _handle_describe_screen(self, text: str) -> Dict[str, Any]:
        """Handle describing what's on screen"""
        return self.screen_analyzer.describe_screen()
    
    def _handle_find_on_screen(self, text: str) -> Dict[str, Any]:
        """Handle finding specific item on screen"""
        item = text.split("find on screen", 1)[1].strip() if "find on screen" in text else text.split("locate on screen", 1)[1].strip()
        return self.screen_analyzer.find_on_screen(item)
    
    # ==================== DICTATION HANDLERS ====================
    
    def _handle_start_dictation(self, text: str) -> Dict[str, Any]:
        """Handle starting continuous dictation mode"""
        if not self.dictation:
            self.tts.speak("Dictation requires speech engine to be initialized")
            return {"success": False, "message": "Speech engine not available", "action": "dictation_error"}
        
        return self.dictation.start_dictation()
    
    def _handle_stop_dictation(self, text: str) -> Dict[str, Any]:
        """Handle stopping dictation mode"""
        if not self.dictation:
            return {"success": False, "message": "Dictation not active", "action": "dictation_inactive"}
        
        return self.dictation.stop_dictation()
    
    def _handle_voice_type(self, text: str) -> Dict[str, Any]:
        """Handle one-time voice typing"""
        if not self.dictation:
            self.tts.speak("Voice typing requires speech engine")
            return {"success": False, "message": "Speech engine not available", "action": "voice_type_error"}
        
        # Extract text to type
        content = text
        for trigger in ["voice type", "type with voice"]:
            if trigger in content:
                content = content.split(trigger, 1)[1].strip()
                break
        
        # Check if should auto-send (press Enter)
        auto_send = "and send" in content or "and enter" in content
        if auto_send:
            content = content.replace("and send", "").replace("and enter", "").strip()
        
        return self.dictation.type_with_voice(content, auto_send)


    def _handle_raw_command(self, text: str) -> Dict[str, Any]:
        """Execute raw shell commands requested by LLM or user"""
        cmd = text
        if "execute" in text:
            cmd = text.split("execute", 1)[1].strip()
        
        self.logger.info(f"Executing raw command: {cmd}")
        self.tts.speak("Executing shell command.")
        
        try:
            # Run command
            result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
            
            output = result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout
            error = result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr
            
            if result.returncode == 0:
                self.logger.info(f"Command success: {output}")
                return {"success": True, "message": f"Output: {output}", "action": "run_shell"}
            else:
                self.logger.error(f"Command failed: {error}")
                return {"success": False, "message": f"Error: {error}", "action": "run_shell_error"}
                
        except Exception as e:
            self.logger.error(f"Raw command execution error: {e}")
            return {"success": False, "message": str(e), "action": "error"}
