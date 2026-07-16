"""
Nova Automation Agent
=====================
Handles automation tasks: running predefined templates, screen analysis,
dictation/voice typing, window management, and taking screenshots.
"""

import time
import logging
from typing import Dict, Any

from modules.agents.agent_base import Agent
from modules.automation_workflows import AutomationWorkflows
from modules.screen_analyzer import ScreenAnalyzer
from modules.dictation_engine import DictationEngine


class AutomationAgent(Agent):
    """Agent responsible for automation, screen vision, dictation, screenshots, and window management."""

    def __init__(self, tts=None, speech=None, **kwargs):
        super().__init__(
            name="AutomationAgent",
            description="Performs window/system automation, screen vision analysis, dictation/typing, and runs templates.",
            **kwargs
        )
        self.tts = tts
        self.speech = speech
        self.capabilities = [
            "run_template", "screen_analyze",
            "dictation", "window_manage", "screenshot"
        ]

        self.workflows = AutomationWorkflows(tts)
        self.screen_analyzer = ScreenAnalyzer(tts)
        self.dictation_engine = DictationEngine(speech, tts) if speech else None

    def _do_execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", "")
        params = task.get("parameters", {})
        raw_text = params.get("raw_text", task.get("original_text", ""))

        if action == "run_template":
            template_name = params.get("template_name", raw_text)
            return self._run_template(template_name)
        elif action == "screen_analyze":
            prompt = params.get("prompt", "What do you see on this screen?")
            return self._screen_analyze(prompt, raw_text)
        elif action == "dictation":
            return self._dictation(params, raw_text)
        elif action == "window_manage":
            return self._window_manage(params, raw_text)
        elif action == "screenshot":
            filename = params.get("filename", None)
            return self._screenshot(filename, raw_text)

        return {"success": False, "message": f"Unknown action: {action}", "action": action}

    def _run_template(self, template_name: str) -> Dict[str, Any]:
        # Clean trigger words
        for trigger in ["automate", "run template", "start routine", "run"]:
            if trigger in template_name.lower():
                template_name = template_name.lower().split(trigger, 1)[1].strip()
                break
        template_name = template_name.replace("my ", "").strip()

        return self.workflows.run_automation_template(template_name)

    def _screen_analyze(self, prompt: str, raw_text: str) -> Dict[str, Any]:
        text = raw_text.lower()
        if "read screen" in text or "what does it say" in text:
            return self.screen_analyzer.read_screen_text()
        elif "describe screen" in text or "describe what you see" in text:
            return self.screen_analyzer.describe_screen()
        elif "find on screen" in text or "locate on screen" in text:
            item = ""
            for trigger in ["find on screen", "locate on screen"]:
                if trigger in text:
                    item = text.split(trigger, 1)[1].strip()
                    break
            if not item:
                item = prompt
            return self.screen_analyzer.find_on_screen(item)

        # Extract custom prompt if present
        for trigger in ["analyze screen", "analyse screen"]:
            if trigger in text:
                custom = raw_text.split(raw_text.lower().find(trigger) + len(trigger))[1].strip()
                if custom:
                    prompt = custom
                break

        return self.screen_analyzer.analyze_screen(prompt)

    def _dictation(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        text = raw_text.lower()
        if not self.dictation_engine:
            return {"success": False, "message": "Speech engine not initialized for dictation", "action": "dictation"}

        if "start" in text or "begin" in text:
            return self.dictation_engine.start_dictation()
        elif "stop" in text or "end" in text or "exit" in text:
            return self.dictation_engine.stop_dictation()
        elif "type" in text:
            content = raw_text
            for trigger in ["voice type", "type with voice", "type"]:
                if trigger in content.lower():
                    idx = content.lower().find(trigger) + len(trigger)
                    content = content[idx:].strip()
                    break
            auto_send = "and send" in content.lower() or "and enter" in content.lower()
            if auto_send:
                content = content.replace("and send", "").replace("and enter", "").strip()
            return self.dictation_engine.type_with_voice(content, auto_send)

        return {"success": False, "message": "Unknown dictation command", "action": "dictation"}

    def _window_manage(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        text = raw_text.lower()
        if any(w in text for w in ["minimize all", "minimise all", "show desktop", "minimize screen"]):
            return self.workflows.minimize_all_windows()
        elif any(w in text for w in ["maximize", "maximise"]) and any(word in text for word in ["window", "screen"]):
            return self.workflows.maximize_window()
        elif any(w in text for w in ["close window", "close this"]):
            return self.workflows.close_current_window()

        return {"success": False, "message": "Unknown window command", "action": "window_manage"}

    def _screenshot(self, filename: str, raw_text: str) -> Dict[str, Any]:
        if not filename:
            text = raw_text.lower()
            if "as" in text or "named" in text:
                trigger = "as" if "as" in text else "named"
                filename = raw_text.split(trigger, 1)[1].strip()

        return self.workflows.take_screenshot(filename)
