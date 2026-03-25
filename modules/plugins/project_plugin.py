from modules.plugins.base import Plugin
import os
import subprocess
import time
import json
from modules.pyautogui_config import safe_type, safe_press
from modules.llm_engine import LLMEngine


class ProjectPlugin(Plugin):
    def __init__(self, core):
        super().__init__(core)
        self.llm = LLMEngine()

    def handle_command(self, text):
        if "set up" in text and "project" in text:
            return self.setup_project(text)
        return None
        
    def vibe_coding(self, prompt):
        """
        AI-Powered Project Generation ("Vibe Coding")
        Generates a full project structure and code based on a description.
        """
        self.core.tts.speak("Thinking about the architecture...")
        
        # 1. Ask LLM for project structure
        system_prompt = """
        You are an expert full-stack developer. 
        The user wants to build an application. 
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
            # We use the LLMEngine to generate the plan
            # We need to bypass the 'decide_action' and query directly or expose a method.
            # Let's use the provider directly if possible or add a method to LLMEngine.
            # For now, we will assume LLMEngine has a specialized method or we rely on the main LLM.
            # Actually, let's just use the decide_action but with a strict context? No, that returns actions.
            
            # Let's add a raw query method to LLM Engine or just instantiate a new query here?
            # Re-using LLM Engine's private methods is messy but effective for this MVP.
            
            if self.llm.provider == "gemini":
                response = self.llm._query_gemini(prompt, system_prompt, "Generate a coding project")
            elif self.llm.provider == "openai":
                response = self.llm._query_openai(prompt, system_prompt, "Generate a coding project")
            else:
                self.core.tts.speak("I need an API key to write code.")
                return {"success": False, "message": "No API key", "action": "error"}
                
            # 2. Parse Response
            project_name = response.get("project_name", "generated_project")
            files = response.get("files", {})
            commands = response.get("commands", [])
            description = response.get("description", "")
            
            # 3. Create Project on Desktop
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            project_path = os.path.join(desktop, project_name)
            
            if os.path.exists(project_path):
                project_path += f"_{int(time.time())}"
                
            os.makedirs(project_path, exist_ok=True)
            self.core.tts.speak(f"Creating project {project_name}.")
            
            # 4. Write Files
            for rel_path, content in files.items():
                full_path = os.path.join(project_path, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                    
            # 5. Open in VS Code
            self.core.tts.speak("Opening in VS Code.")
            subprocess.Popen(["code", project_path], shell=True)
            time.sleep(5) # Wait for load
            
            # 6. Run commands?
            # Creating a setup script is safer than running commands blindly in a loop.
            if commands:
                setup_bat = os.path.join(project_path, "setup_and_run.bat")
                with open(setup_bat, "w") as f:
                    f.write("@echo off\n")
                    f.write("echo Setting up project...\n")
                    for cmd in commands:
                        f.write(f"call {cmd}\n")
                    f.write("pause\n")
                
                self.core.tts.speak("I've created a setup script. Running it now.")
                # Open terminal in VS Code and run it? Or just run in new window?
                subprocess.Popen(["start", setup_bat], shell=True, cwd=project_path)

            return {"success": True, "message": f"vibe coded {project_name}: {description}", "action": "vibe_code"}
            
        except Exception as e:
            self.core.logger.error(f"Vibe coding failed: {e}")
            self.core.tts.speak("Something went wrong while generating the code.")
            return {"success": False, "message": str(e), "action": "error"}


    def setup_project(self, text):
        """
        Sets up a new project folder.
        "Nova set up a new project folder."
        """
        self.core.tts.speak("Setting up a new project.")
        
        # 1. Create folder
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        project_name = "New_Project_" + str(int(time.time()))
        project_path = os.path.join(desktop, project_name)
        
        os.makedirs(project_path, exist_ok=True)
        self.core.tts.speak(f"Created folder {project_name} on Desktop.")
        
        # 2. Open VS Code
        self.core.tts.speak("Opening VS Code in the new directory.")
        subprocess.Popen(["code", project_path], shell=True)
        time.sleep(5) # Wait for VS Code to open
        
        # 3. Create starter files
        self.core.tts.speak("Creating starter files.")
        # We can write files directly using python
        with open(os.path.join(project_path, "index.html"), "w") as f:
            f.write("<!DOCTYPE html>\n<html>\n<body>\n<h1>Hello World</h1>\n</body>\n</html>")
        with open(os.path.join(project_path, "style.css"), "w") as f:
            f.write("body { background: #f0f0f0; }")
        with open(os.path.join(project_path, "script.js"), "w") as f:
            f.write("console.log('Hello from Nova');")
            
        # 4. Initialize git
        self.core.tts.speak("Initializing Git repository.")
        try:
            subprocess.run(["git", "init"], cwd=project_path, check=True)
        except Exception as e:
            self.core.logger.error(f"Git init failed: {e}")
            self.core.tts.speak("Git initialization failed, but project is ready.")
            
        # 5. Open terminal (VS Code usually opens with one, or we can toggle it)
        self.core.tts.speak("Opening terminal.")
        safe_press('ctrl', '`') # Toggle terminal shortcut
        
        return {"success": True, "message": f"Project {project_name} setup complete", "action": "setup_project"}
