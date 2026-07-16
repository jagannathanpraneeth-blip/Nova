"""
Nova Meta-Agent
===============
Allows the system to be self-expanding by creating, compiling,
and hot-loading new specialist agents at runtime.
"""

import os
import sys
import ast
import logging
import importlib.util
from typing import Dict, Any

from modules.agents.agent_base import Agent, AgentState


class MetaAgent(Agent):
    """Specialized agent that generates, writes, compiles, and registers new agents at runtime."""

    def __init__(self, tts=None, registry=None, **kwargs):
        super().__init__(
            name="MetaAgent",
            description="Allows self-expansion of Nova. Generates, compiles, and loads new custom agents dynamically.",
            **kwargs
        )
        self.tts = tts
        self.registry = registry
        self.capabilities = ["create_agent", "list_agents", "kill_agent"]
        self.dynamic_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dynamic')

    def _do_execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", "")
        params = task.get("parameters", {})
        raw_text = params.get("raw_text", task.get("original_text", ""))

        if action == "create_agent":
            name = params.get("name", "")
            description = params.get("description", "")
            if not name or not description:
                # LLM might pass it in query
                name = params.get("app_name", "") # fallback
                description = raw_text
            return self._create_agent(name, description)
        elif action == "list_agents":
            return self._list_agents()
        elif action == "kill_agent":
            agent_id = params.get("agent_id", "")
            return self._kill_agent(agent_id)

        return {"success": False, "message": f"Unknown action: {action}", "action": action}

    def _create_agent(self, name: str, description: str) -> Dict[str, Any]:
        """Creates and registers a new dynamic agent at runtime."""
        if not name:
            # Generate a name based on description
            system_prompt = "Suggest a single CamelCase name for an agent that does: " + description + ". Return name only (e.g. BatteryAgent)."
            name = self.ask_llm("", system_prompt).strip().replace(" ", "").replace('"', '').replace("'", "")
            if not name.endswith("Agent"):
                name += "Agent"

        # Sanitize name
        name = "".join(c for c in name if c.isalnum())
        if not name:
            name = "DynamicAgent"

        self.logger.info(f"Generating agent code for '{name}' with description: '{description}'")
        if self.tts:
            self.tts.speak(f"Creating a new custom agent named {name}.")

        system_prompt = f"""
        You are the Meta-Agent code generator.
        Create a new Python class '{name}' that inherits from 'modules.agents.agent_base.Agent'.
        The agent description is: "{description}".
        
        Guidelines:
        1. Inherit from 'Agent'.
        2. Set self.name = '{name}' and self.description in the __init__.
        3. Define self.capabilities (a list of string action names this agent handles).
        4. Implement '_do_execute(self, task: Dict[str, Any]) -> Dict[str, Any]'. It should inspect task['action'], run local python code or call system subprocesses, and return a dictionary like {{"success": True, "message": "Result string", "action": task['action']}}.
        5. DO NOT import any dangerous libraries or execute arbitrary system formatting.
        6. Rely on standard Python libraries like `os`, `sys`, `time`, `subprocess`, `urllib`, `re`, `json`, `datetime` or pyqt6 / pyautogui (since they are preinstalled in Nova's environment).
        7. Make sure to define the capabilities cleanly so the Orchestrator can route tasks matching those capabilities to this agent.
        8. Return ONLY clean Python code. Do not include markdown code block backticks.
        """

        prompt = f"Write the Python class file for '{name}'."
        code = self.ask_llm(prompt, system_prompt).strip()

        # Clean markdown code block markers
        if code.startswith("```python"):
            code = code.split("```python", 1)[1]
        elif code.startswith("```"):
            code = code.split("```", 1)[1]
        if code.endswith("```"):
            code = code.rsplit("```", 1)[0]
        code = code.strip()

        # Ensure dynamic directory exists
        os.makedirs(self.dynamic_dir, exist_ok=True)
        file_name = f"{name.lower()}.py"
        file_path = os.path.join(self.dynamic_dir, file_name)

        try:
            # Validate Syntax using AST
            ast.parse(code)
            self.logger.info("AST syntax check passed successfully.")

            # Write code to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            # Hot-load module dynamically
            spec = importlib.util.spec_from_file_location(f"modules.agents.dynamic.{name.lower()}", file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Find the class and instantiate it
            agent_class = getattr(module, name, None)
            if not agent_class:
                # Find any subclass of Agent in the module
                from modules.agents.agent_base import Agent as BaseAgent
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BaseAgent) and attr != BaseAgent:
                        agent_class = attr
                        break

            if not agent_class:
                return {"success": False, "message": f"Class '{name}' not found in generated code", "action": "create_agent"}

            # Instantiate and register
            # Pass tts reference if class accepts it, or just kwargs
            import inspect
            sig = inspect.signature(agent_class.__init__)
            if 'tts' in sig.parameters:
                new_agent = agent_class(tts=self.tts)
            else:
                new_agent = agent_class()

            # Wire systems
            new_agent._message_bus = self._message_bus
            new_agent._memory = self._memory
            new_agent._llm_engine = self._llm_engine
            new_agent._registry = self.registry

            # Register
            success = self.registry.register(new_agent)
            if success:
                msg = f"Agent {name} has been successfully created, compiled, and registered into the system."
                if self.tts:
                    self.tts.speak(msg)
                return {"success": True, "message": msg, "action": "create_agent"}
            else:
                return {"success": False, "message": "Registry registration failed", "action": "create_agent"}

        except SyntaxError as se:
            self.logger.error(f"Syntax validation failed for generated agent {name}: {se}")
            return {"success": False, "message": f"Generated code had syntax errors: {se}", "action": "create_agent"}
        except Exception as e:
            self.logger.error(f"Failed to compile or load dynamic agent {name}: {e}", exc_info=True)
            return {"success": False, "message": str(e), "action": "create_agent"}

    def _list_agents(self) -> Dict[str, Any]:
        """Lists all registered agents and states."""
        agents = self.registry.list_all()
        formatted = "\n".join([f"- {a['name']} ({a['agent_id']}) Status: {a['state']}" for a in agents])
        return {"success": True, "message": f"Active agents:\n{formatted}", "action": "list_agents"}

    def _kill_agent(self, agent_id: str) -> Dict[str, Any]:
        """Kills/deregisters a dynamic agent."""
        if not agent_id:
            return {"success": False, "message": "No agent ID specified to kill", "action": "kill_agent"}

        success = self.registry.deregister(agent_id)
        if success:
            msg = f"Agent {agent_id} has been terminated and removed from the active registry."
            if self.tts:
                self.tts.speak(msg)
            return {"success": True, "message": msg, "action": "kill_agent"}
        else:
            return {"success": False, "message": f"Failed to deregister agent {agent_id}", "action": "kill_agent"}
