import json
import os
import subprocess
import logging
from typing import List, Dict, Any
from datetime import datetime

class ClipboardManager:
    """
    Manages text snippets from the system clipboard.
    Allocates storage for snippets and allows searching/retrieval.
    """
    
    def __init__(self, data_dir: str):
        self.logger = logging.getLogger('ClipboardManager')
        self.data_file = os.path.join(data_dir, 'snippets.json')
        self.snippets = self._load_snippets()

    def _load_snippets(self) -> List[Dict[str, Any]]:
        """Load snippets from disk"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load snippets: {e}")
                return []
        return []

    def _save_to_disk(self):
        """Save current snippets to disk"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.snippets, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save snippets: {e}")

    def get_clipboard_content(self) -> str:
        """Get current text content from Windows clipboard using PowerShell"""
        try:
            # Use PowerShell to get clipboard text - reliable on Windows without extra deps
            cmd = ["powershell", "-command", "Get-Clipboard"]
            # specialized for windows
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Failed to get clipboard: {e}")
            return ""

    def save_snippet(self, description: str = "general") -> str:
        """Save current clipboard content as a snippet"""
        content = self.get_clipboard_content()
        if not content:
            return "Clipboard is empty or contains non-text data."

        # Check for duplicates (exact match)
        for s in self.snippets:
            if s['content'] == content:
                return "This snippet is already saved."

        snippet = {
            "id": len(self.snippets) + 1,
            "content": content,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "preview": content[:30].replace("\n", " ") + "..." if len(content) > 30 else content
        }
        
        self.snippets.append(snippet)
        self._save_to_disk()
        return f"Saved snippet: {description}"

    def find_snippets(self, query: str) -> List[Dict[str, Any]]:
        """Find snippets matching a query (tag or content)"""
        # If query is generic like "my snippets", return recent ones
        if query in ["my snippets", "all snippets", "snippets"]:
            return self.snippets[-5:] # Return last 5
            
        query = query.lower()
        results = []
        for s in self.snippets:
            if query in s['description'].lower() or query in s['content'].lower():
                results.append(s)
        return results
