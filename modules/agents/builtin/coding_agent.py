"""
Nova Coding Agent
=================
Handles software engineering tasks: dynamic project setup, code generation (vibe coding),
running shell commands, and debugging support.
"""

import os
import subprocess
import time
import json
import logging
from typing import Dict, Any

from modules.agents.agent_base import Agent
from modules.pyautogui_config import safe_press


class CodingAgent(Agent):
    """Agent responsible for writing code, setting up repositories, and running CLI commands."""

    def __init__(self, tts=None, **kwargs):
        super().__init__(
            name="CodingAgent",
            description="Specializes in generating code (Vibe Coding), creating projects, and running shell commands.",
            **kwargs
        )
        self.tts = tts
        self.capabilities = ["vibe_code", "setup_project", "run_shell"]

    def _do_execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", "")
        params = task.get("parameters", {})
        raw_text = params.get("raw_text", task.get("original_text", ""))

        if action == "vibe_code":
            prompt = params.get("prompt", raw_text)
            return self._vibe_coding(prompt)
        elif action == "setup_project":
            return self._setup_project(raw_text)
        elif action == "run_shell":
            command = params.get("command", raw_text)
            return self._run_shell(command)

        return {"success": False, "message": f"Unknown action: {action}", "action": action}

    def _vibe_coding(self, prompt: str) -> Dict[str, Any]:
        """Generates a complete project based on the prompt."""
        if not prompt:
            return {"success": False, "message": "No prompt provided", "action": "vibe_code"}

        if self.tts:
            self.tts.speak("Thinking about the architecture...")

        system_prompt = """
        You are an expert developer. The user wants to build an application.
        Return a JSON object with the following structure:
        {
            "project_name": "snake_case_name",
            "files": {
                "filename.ext": "full code content...",
                "folder/filename.ext": "full code content..."
            },
            "commands": ["command to run to install dependencies", "command to run app"],
            "description": "Short description of what has been built"
        }
        Create a COMPLETE, WORKING MVP.
        If it's a web app, include HTML, CSS, JS.
        If it's python, include requirements.txt.
        """

        try:
            response = self.ask_llm_json(prompt, system_prompt)
            if not response:
                if self.tts:
                    self.tts.speak("I was unable to structure the project using the AI engine.")
                return {"success": False, "message": "Failed to parse JSON from LLM", "action": "vibe_code"}

            project_name = response.get("project_name", "generated_project")
            files = response.get("files", {})
            commands = response.get("commands", [])
            description = response.get("description", "")

            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            project_path = os.path.join(desktop, project_name)

            if os.path.exists(project_path):
                project_path += f"_{int(time.time())}"

            os.makedirs(project_path, exist_ok=True)
            if self.tts:
                self.tts.speak(f"Creating project {project_name}.")

            for rel_path, content in files.items():
                full_path = os.path.join(project_path, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

            if self.tts:
                self.tts.speak("Opening in VS Code.")
            subprocess.Popen(["code", project_path], shell=True)
            time.sleep(5)

            if commands:
                setup_bat = os.path.join(project_path, "setup_and_run.bat")
                with open(setup_bat, "w") as f:
                    f.write("@echo off\n")
                    f.write("echo Setting up project...\n")
                    for cmd in commands:
                        f.write(f"call {cmd}\n")
                    f.write("pause\n")

                if self.tts:
                    self.tts.speak("Running setup script.")
                subprocess.Popen(["start", setup_bat], shell=True, cwd=project_path)

            return {"success": True, "message": f"Vibe coded {project_name}: {description}", "action": "vibe_code"}

        except Exception as e:
            self.logger.error(f"Vibe coding failed: {e}")
            if self.tts:
                self.tts.speak("Something went wrong while generating the code.")
            return {"success": False, "message": str(e), "action": "vibe_code"}

    def _setup_project(self, raw_text: str) -> Dict[str, Any]:
        """Sets up a new empty web project folder."""
        if self.tts:
            self.tts.speak("Setting up a new project.")

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        project_name = "New_Project_" + str(int(time.time()))
        project_path = os.path.join(desktop, project_name)

        os.makedirs(project_path, exist_ok=True)
        if self.tts:
            self.tts.speak(f"Created folder {project_name} on Desktop.")

        # Create starter files
        with open(os.path.join(project_path, "index.html"), "w") as f:
            f.write("<!DOCTYPE html>\n<html>\n<body>\n<h1>Hello World</h1>\n</body>\n</html>")
        with open(os.path.join(project_path, "style.css"), "w") as f:
            f.write("body { background: #f0f0f0; }")
        with open(os.path.join(project_path, "script.js"), "w") as f:
            f.write("console.log('Hello from Nova');")

        try:
            subprocess.run(["git", "init"], cwd=project_path, check=True)
        except Exception as e:
            self.logger.error(f"Git init failed: {e}")

        if self.tts:
            self.tts.speak("Opening VS Code.")
        subprocess.Popen(["code", project_path], shell=True)
        time.sleep(5)
        safe_press('ctrl', '`') # Toggle terminal shortcut

        return {"success": True, "message": f"Project {project_name} setup complete", "action": "setup_project"}

    def _run_shell(self, command: str) -> Dict[str, Any]:
        """Executes a PowerShell command."""
        # Clean up command string
        for trigger in ["execute", "run command", "powershell"]:
            if trigger in command.lower():
                command = command.lower().split(trigger, 1)[1].strip()
                break

        if not command:
            return {"success": False, "message": "No command to execute", "action": "run_shell"}

        self.logger.info(f"Executing command: {command}")
        if self.tts:
            self.tts.speak("Executing shell command.")

        try:
            result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True, timeout=15)
            output = result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout
            error = result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr

            if result.returncode == 0:
                return {"success": True, "message": f"Output: {output}", "action": "run_shell"}
            else:
                return {"success": False, "message": f"Error: {error}", "action": "run_shell"}
        except Exception as e:
            self.logger.error(f"Command execution crashed: {e}")
            return {"success": False, "message": str(e), "action": "run_shell"}
