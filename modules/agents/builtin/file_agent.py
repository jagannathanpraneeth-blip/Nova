"""
Nova File Agent
===============
Handles file operations: natural language file search, quick notes creation,
and managing clipboard snippets.
"""

import os
import subprocess
import time
import logging
from typing import Dict, Any, List
from datetime import datetime

from modules.agents.agent_base import Agent
from modules.file_searcher import FileSearcher
from modules.clipboard_manager import ClipboardManager
from config import DATA_DIR


class FileAgent(Agent):
    """Agent responsible for file search, note taking, and clipboard snippet management."""

    def __init__(self, tts=None, **kwargs):
        super().__init__(
            name="FileAgent",
            description="Manages files: search, quick notepad notes, and saving/finding clipboard snippets.",
            **kwargs
        )
        self.tts = tts
        self.capabilities = ["find_files", "create_note", "clipboard_manage"]
        self.file_searcher = FileSearcher()
        self.clipboard_manager = ClipboardManager(DATA_DIR)

    def _do_execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", "")
        params = task.get("parameters", {})
        raw_text = params.get("raw_text", task.get("original_text", ""))

        if action == "find_files":
            query = params.get("query", raw_text)
            return self._find_files(query)
        elif action == "create_note":
            note_text = params.get("note_text", raw_text)
            return self._create_note(note_text)
        elif action == "clipboard_manage":
            return self._clipboard_manage(params, raw_text)

        return {"success": False, "message": f"Unknown action: {action}", "action": action}

    def _find_files(self, query: str) -> Dict[str, Any]:
        """Search for files using natural language query."""
        # Clean query
        for trigger in ["find file", "search file", "search for file", "look for file", "open file about"]:
            if trigger in query.lower():
                query = query.lower().split(trigger, 1)[1].strip()
                break

        if self.tts:
            self.tts.speak("Searching for files...")

        results = self.file_searcher.search(query)
        if not results:
            msg = "I couldn't find any matching files."
            if self.tts:
                self.tts.speak(msg)
            return {"success": False, "message": msg, "action": "find_files"}

        top_match = results[0]

        # Auto-open if "open" is in the intent
        if "open" in query.lower() or "run" in query.lower():
            if self.tts:
                self.tts.speak(f"Opening {top_match['name']}")
            try:
                os.startfile(top_match['path'])
                return {"success": True, "message": f"Opened {top_match['name']}", "action": "open_file"}
            except Exception as e:
                self.logger.error(f"Failed to open file: {e}")
                return {"success": False, "message": str(e), "action": "open_file"}

        msg = f"I found {len(results)} matching files. The top match is {top_match['name']}."
        if self.tts:
            self.tts.speak(msg)

        formatted_results = "\n".join([f"- {r['name']} (Score: {r['score']}, Path: {r['path']})" for r in results])
        return {"success": True, "message": formatted_results, "action": "find_files"}

    def _create_note(self, note_text: str) -> Dict[str, Any]:
        """Creates a quick note in Notepad."""
        for trigger in ["create note", "make note", "take note", "saying", "that says"]:
            if trigger in note_text.lower():
                note_text = note_text.lower().split(trigger, 1)[1].strip()
                break

        if not note_text:
            note_text = "Empty Note"

        try:
            subprocess.Popen(["notepad.exe"])
            time.sleep(1)
            from modules.pyautogui_config import safe_type
            safe_type(note_text, interval=0.05)

            msg = "Note created in Notepad"
            if self.tts:
                self.tts.speak(msg)
            return {"success": True, "message": msg, "action": "create_note"}
        except Exception as e:
            self.logger.error(f"Note error: {e}")
            if self.tts:
                self.tts.speak("Failed to create note")
            return {"success": False, "message": str(e), "action": "create_note"}

    def _clipboard_manage(self, params: Dict, raw_text: str) -> Dict[str, Any]:
        """Manages snippets from the system clipboard."""
        text = raw_text.lower()

        if "save" in text or "remember" in text:
            description = "general"
            if " as " in text:
                description = text.split(" as ", 1)[1].strip()
            elif " about " in text:
                description = text.split(" about ", 1)[1].strip()
            elif " named " in text:
                description = text.split(" named ", 1)[1].strip()

            result = self.clipboard_manager.save_snippet(description)
            if self.tts:
                self.tts.speak(result)
            return {"success": True, "message": result, "action": "save_snippet"}

        elif any(w in text for w in ["show", "find", "read", "get", "list"]):
            query = "all snippets"
            if " about " in text:
                query = text.split(" about ", 1)[1].strip()
            elif " for " in text:
                query = text.split(" for ", 1)[1].strip()

            snippets = self.clipboard_manager.find_snippets(query)
            if not snippets:
                msg = f"No snippets found for {query}"
                if self.tts:
                    self.tts.speak(msg)
                return {"success": False, "message": msg, "action": "find_snippets"}

            if self.tts:
                self.tts.speak(f"Found {len(snippets)} snippets.")

            msg_out = "Here are your snippets:\n"
            for s in snippets:
                msg_out += f"- [{s['description']}] {s['preview']}\n"
            return {"success": True, "message": msg_out, "action": "list_snippets"}

        return {"success": False, "message": "Unknown clipboard command", "action": "clipboard_manage"}
