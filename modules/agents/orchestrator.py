"""
Nova Orchestrator
=================
The central intelligence of the multi-agent system.
Replaces AIBrain as the system's brain.

Uses LLM to:
1. Decompose complex tasks into sub-tasks
2. Route sub-tasks to the best available agents
3. Execute agents in parallel when possible
4. Synthesize results into a unified response
5. Maintain conversation context
"""

import json
import logging
import threading
import time
from typing import Dict, Any, List, Optional

from modules.agents.agent_base import Agent, AgentState
from modules.agents.agent_registry import AgentRegistry
from modules.agents.message_bus import MessageBus
from modules.agents.memory import SharedMemory
from modules.llm_engine import LLMEngine
from modules.task_queue import execute_async, get_task_queue


class Orchestrator:
    """
    The Orchestrator decomposes user requests into agent tasks,
    delegates to specialist agents, and synthesizes results.
    """
    
    def __init__(self, tts_engine, speech_engine=None):
        self.logger = logging.getLogger("Orchestrator")
        self.tts = tts_engine
        self.speech = speech_engine
        
        # Core systems
        self.registry = AgentRegistry()
        self.message_bus = MessageBus()
        self.memory = SharedMemory()
        self.llm_engine = LLMEngine()
        
        # Wire message bus to registry
        self.message_bus.set_registry(self.registry)
        
        # Track active multi-step tasks
        self._active_plans: Dict[str, Dict] = {}
        self._plan_lock = threading.Lock()
        
        # Initialize built-in agents
        self._register_builtin_agents()
        
        # Wire services to all agents
        self.registry.wire_services(
            message_bus=self.message_bus,
            memory=self.memory,
            llm_engine=self.llm_engine
        )
        
        self.logger.info(
            f"Orchestrator ready. {self.registry.get_agent_count()} agents registered. "
            f"LLM: {self.llm_engine.provider or 'none'}"
        )
    
    def _register_builtin_agents(self):
        """Register all built-in specialist agents."""
        try:
            from modules.agents.builtin.system_agent import SystemAgent
            self.registry.register(SystemAgent(tts=self.tts))
        except Exception as e:
            self.logger.error(f"Failed to register SystemAgent: {e}")
        
        try:
            from modules.agents.builtin.web_agent import WebAgent
            self.registry.register(WebAgent(tts=self.tts))
        except Exception as e:
            self.logger.error(f"Failed to register WebAgent: {e}")
        
        try:
            from modules.agents.builtin.coding_agent import CodingAgent
            self.registry.register(CodingAgent(tts=self.tts))
        except Exception as e:
            self.logger.error(f"Failed to register CodingAgent: {e}")
        
        try:
            from modules.agents.builtin.file_agent import FileAgent
            self.registry.register(FileAgent(tts=self.tts))
        except Exception as e:
            self.logger.error(f"Failed to register FileAgent: {e}")
        
        try:
            from modules.agents.builtin.communication_agent import CommunicationAgent
            self.registry.register(CommunicationAgent(tts=self.tts))
        except Exception as e:
            self.logger.error(f"Failed to register CommunicationAgent: {e}")
        
        try:
            from modules.agents.builtin.automation_agent import AutomationAgent
            self.registry.register(AutomationAgent(tts=self.tts, speech=self.speech))
        except Exception as e:
            self.logger.error(f"Failed to register AutomationAgent: {e}")
        
        try:
            from modules.agents.builtin.research_agent import ResearchAgent
            self.registry.register(ResearchAgent(tts=self.tts))
        except Exception as e:
            self.logger.error(f"Failed to register ResearchAgent: {e}")
        
        try:
            from modules.agents.builtin.meta_agent import MetaAgent
            self.registry.register(MetaAgent(tts=self.tts, registry=self.registry))
        except Exception as e:
            self.logger.error(f"Failed to register MetaAgent: {e}")
    
    # ── Main Entry Point ──────────────────────────────────────────────
    
    def process(self, text: str) -> Dict[str, Any]:
        """
        Process a user command through the multi-agent system.
        
        Flow:
        1. Log conversation
        2. Use LLM to decompose into agent tasks
        3. Route tasks to agents
        4. Collect and synthesize results
        5. Return unified response
        """
        if not text:
            return {"success": False, "message": "No input provided", "action": "none"}
        
        text = text.strip()
        self.logger.info(f"Orchestrator processing: {text}")
        
        # Store in memory
        self.memory.add_conversation("user", text)
        
        # If no LLM available, use capability-matching fallback
        if not self.llm_engine.provider:
            return self._fallback_routing(text)
        
        # Use LLM to create an execution plan
        try:
            plan = self._create_plan(text)
            self.logger.info(f"Execution plan: {json.dumps(plan, indent=2)}")
        except Exception as e:
            self.logger.error(f"Planning failed: {e}", exc_info=True)
            return self._fallback_routing(text)
        
        # Execute the plan
        result = self._execute_plan(plan, text)
        
        # Store response in memory
        self.memory.add_conversation("nova", result.get("message", ""), 
                                     metadata={"action": result.get("action")})
        
        # Log task
        self.memory.log_task(
            agent_name="orchestrator",
            action=result.get("action", "unknown"),
            success=result.get("success", False),
            details=text
        )
        
        return result
    
    # ── LLM Planning ──────────────────────────────────────────────────
    
    def _create_plan(self, user_input: str) -> Dict[str, Any]:
        """Use LLM to decompose user input into an execution plan."""
        
        agent_manifest = self.registry.get_manifest()
        conversation_context = self.memory.get_conversation_context(limit=5)
        active_goals = self.memory.get_active_goals()
        
        goals_text = ""
        if active_goals:
            goals_text = "\nACTIVE GOALS:\n"
            for gid, g in active_goals.items():
                goals_text += f"  - {gid}: {g['description']} (progress: {g['progress']}%)\n"
        
        system_prompt = self._get_orchestrator_prompt(agent_manifest, goals_text)
        
        user_prompt = f"""Recent conversation:
{conversation_context}

Current request: {user_input}

Analyze this request and create an execution plan. Respond with JSON only."""
        
        # Query LLM
        if self.llm_engine.provider == "gemini":
            import google.generativeai as genai
            model = genai.GenerativeModel(self.llm_engine.model_name)
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = model.generate_content(full_prompt)
            raw = response.text
        elif self.llm_engine.provider == "openai":
            response = self.llm_engine.client.chat.completions.create(
                model=self.llm_engine.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            raw = response.choices[0].message.content
        else:
            return {"steps": [{"action": "conversation", "response": "I need an API key to process this."}]}
        
        # Parse JSON
        text = raw
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        return json.loads(text.strip())
    
    def _get_orchestrator_prompt(self, agent_manifest: str, goals_text: str) -> str:
        """Build the orchestrator's system prompt."""
        return f"""You are the ORCHESTRATOR of Nova, an advanced multi-agent AI system.
Your job is to decompose user requests into execution plans and route them to specialist agents.

{agent_manifest}
{goals_text}

INSTRUCTIONS:
1. Analyze the user's request and determine which agent(s) should handle it.
2. For simple requests, create a single-step plan.
3. For complex requests, break them into sequential or parallel steps.
4. Each step must target a specific agent capability.
5. For conversational requests (greetings, questions about Nova), handle directly with a "conversation" action.

OUTPUT FORMAT (JSON):
{{
    "thought": "Your reasoning about how to handle this request",
    "response": "Natural language response to speak to the user. Be professional, intelligent, and concise. Address user as 'Sir'.",
    "steps": [
        {{
            "agent_capability": "the_capability_to_use",
            "action": "specific_action_name",
            "parameters": {{}},
            "parallel": false
        }}
    ]
}}

SPECIAL ACTIONS:
- "conversation": No agent needed, just respond. Use for greetings, identity questions, chitchat.
- "create_agent": Route to MetaAgent when user wants to create a new custom agent.
- "set_goal": When user sets a long-term goal or recurring task.

EXAMPLES:

User: "Open Chrome and search for Python tutorials"
{{
    "thought": "Two sequential actions: open browser then search",
    "response": "Opening Chrome and searching for Python tutorials, Sir.",
    "steps": [
        {{"agent_capability": "open_app", "action": "open_app", "parameters": {{"app_name": "chrome"}}, "parallel": false}},
        {{"agent_capability": "web_search", "action": "web_search", "parameters": {{"query": "Python tutorials"}}, "parallel": false}}
    ]
}}

User: "Who are you?"
{{
    "thought": "Identity question, handle as conversation",
    "response": "I am Nova, an advanced autonomous multi-agent AI system. I have {self.registry.get_agent_count()} specialized agents at my disposal, each designed for specific tasks. I can control your computer, search the web, write code, manage files, and even create new agents on the fly. How may I assist you, Sir?",
    "steps": [{{"agent_capability": "conversation", "action": "conversation", "parameters": {{}}, "parallel": false}}]
}}

User: "Create an agent that monitors my battery"
{{
    "thought": "User wants a new custom agent. Route to MetaAgent.",
    "response": "Creating a custom battery monitoring agent for you, Sir.",
    "steps": [{{"agent_capability": "create_agent", "action": "create_agent", "parameters": {{"description": "Monitor battery level and alert when low", "name": "BatteryMonitorAgent"}}, "parallel": false}}]
}}

CRITICAL:
- Respond ONLY with valid JSON.
- Always include "thought", "response", and "steps".
- Match capabilities exactly to agent capabilities listed above.
- Use "conversation" action for non-actionable requests.
- Be proactive: if user asks "how do I...", DO the thing instead of explaining.
"""
    
    # ── Plan Execution ────────────────────────────────────────────────
    
    def _execute_plan(self, plan: Dict, original_text: str) -> Dict[str, Any]:
        """Execute an LLM-generated plan by routing steps to agents."""
        
        response = plan.get("response", "")
        thought = plan.get("thought", "")
        steps = plan.get("steps", [])
        
        self.logger.info(f"Executing plan: thought='{thought}', steps={len(steps)}")
        
        if not steps:
            # Pure conversation
            if response:
                self.tts.speak(response)
            return {"success": True, "message": response, "action": "conversation"}
        
        # Check for pure conversation action
        if len(steps) == 1 and steps[0].get("action") == "conversation":
            if response:
                self.tts.speak(response)
            return {"success": True, "message": response, "action": "conversation"}
        
        # Speak the response first (non-blocking feedback)
        if response:
            self.tts.speak(response)
        
        # Group steps: parallel vs sequential
        parallel_steps = [s for s in steps if s.get("parallel", False)]
        sequential_steps = [s for s in steps if not s.get("parallel", False)]
        
        all_results = []
        
        # Execute parallel steps first
        if parallel_steps:
            futures = []
            for step in parallel_steps:
                task_id = execute_async(self._execute_step, step, original_text)
                futures.append(task_id)
            
            # Wait for parallel tasks (with timeout)
            tq = get_task_queue()
            for task_id in futures:
                result = tq.wait_for_task(task_id, timeout=30)
                if result["status"] == "completed" and result["result"]:
                    all_results.append(result["result"])
        
        # Execute sequential steps
        for step in sequential_steps:
            result = self._execute_step(step, original_text)
            all_results.append(result)
            
            # If a step fails, we may still continue (unless critical)
            if not result.get("success", False):
                self.logger.warning(f"Step failed: {step.get('action')} - {result.get('message')}")
        
        # Synthesize results
        return self._synthesize_results(all_results, response)
    
    def _execute_step(self, step: Dict, original_text: str) -> Dict[str, Any]:
        """Execute a single step by routing to the appropriate agent."""
        capability = step.get("agent_capability", "")
        action = step.get("action", "")
        parameters = step.get("parameters", {})
        
        self.logger.info(f"Executing step: capability={capability}, action={action}")
        
        # Find the best agent for this capability
        agent = self.registry.find_best_agent(capability)
        
        if not agent:
            # Try matching by action name as fallback
            agent = self.registry.find_best_agent(action)
        
        if not agent:
            self.logger.warning(f"No agent found for capability '{capability}' / action '{action}'")
            return {
                "success": False, 
                "message": f"No agent available for '{capability}'",
                "action": action
            }
        
        self.logger.info(f"Routing to agent: {agent.name} ({agent.agent_id})")
        
        # Build task for the agent
        task = {
            "action": action,
            "parameters": parameters,
            "original_text": original_text
        }
        
        # Execute
        result = agent.execute(task)
        
        # Log to memory
        self.memory.log_task(
            agent_name=agent.name,
            action=action,
            success=result.get("success", False),
            details=str(parameters)
        )
        
        return result
    
    def _synthesize_results(self, results: List[Dict], spoken_response: str) -> Dict[str, Any]:
        """Combine results from multiple agent executions into a single response."""
        if not results:
            return {"success": True, "message": spoken_response or "Done.", "action": "orchestrated"}
        
        # If only one result, return it with the spoken response
        if len(results) == 1:
            result = results[0]
            result["message"] = result.get("message", spoken_response)
            return result
        
        # Multiple results - check overall success
        all_success = all(r.get("success", False) for r in results)
        any_success = any(r.get("success", False) for r in results)
        
        # Build combined message
        messages = []
        actions = []
        for r in results:
            if r.get("message"):
                messages.append(r["message"])
            if r.get("action"):
                actions.append(r["action"])
        
        return {
            "success": any_success,
            "message": spoken_response or " | ".join(messages),
            "action": "multi_agent_" + "_".join(actions[:3]),
            "details": results
        }
    
    # ── Fallback Routing ──────────────────────────────────────────────
    
    def _fallback_routing(self, text: str) -> Dict[str, Any]:
        """
        Simple keyword-based routing when LLM is unavailable.
        Maps keywords to agent capabilities.
        """
        text_lower = text.lower()
        
        # Capability keyword mapping
        routing_table = [
            (["open", "launch", "start", "run"], "open_app"),
            (["close", "kill", "stop", "exit"], "close_app"),
            (["search", "google", "find", "look up"], "web_search"),
            (["go to", "navigate", "visit", "browse"], "navigate_url"),
            (["play", "youtube", "video", "music", "song"], "youtube_play"),
            (["type", "write", "enter"], "type_text"),
            (["click", "mouse", "scroll", "cursor"], "mouse_control"),
            (["press", "key", "shortcut", "ctrl", "alt"], "keyboard_control"),
            (["screenshot", "screen capture"], "screenshot"),
            (["analyze screen", "what's on screen", "read screen"], "screen_analyze"),
            (["whatsapp", "send message"], "send_whatsapp"),
            (["email", "gmail"], "send_email"),
            (["remind", "reminder"], "set_reminder"),
            (["create note", "take note"], "create_note"),
            (["find file", "search file", "search document"], "find_files"),
            (["shutdown", "restart", "sleep", "lock"], "system_command"),
            (["volume", "brightness", "mute"], "volume_control"),
            (["create agent", "new agent", "make agent"], "create_agent"),
            (["code", "build", "create app", "make website", "vibe code"], "vibe_code"),
            (["execute", "powershell", "command"], "run_shell"),
            (["time", "clock"], "system_info"),
            (["date", "today", "what day"], "system_info"),
            (["hello", "hi", "hey", "good morning"], "conversation"),
            (["bye", "goodbye", "good night"], "conversation"),
            (["thanks", "thank you"], "conversation"),
            (["who are you", "what are you", "your name"], "conversation"),
        ]
        
        matched_capability = None
        for keywords, capability in routing_table:
            if any(kw in text_lower for kw in keywords):
                matched_capability = capability
                break
        
        if matched_capability == "conversation":
            # Handle conversation directly
            greetings = ["hello", "hi", "hey", "good morning", "good evening"]
            if any(g in text_lower for g in greetings):
                msg = "Hello, Sir! How may I assist you?"
                self.tts.speak(msg)
                return {"success": True, "message": msg, "action": "greeting"}
            elif "bye" in text_lower or "goodbye" in text_lower:
                msg = "Goodbye, Sir. Shutting down."
                self.tts.speak(msg)
                return {"success": True, "message": msg, "action": "goodbye"}
            elif "thanks" in text_lower or "thank you" in text_lower:
                msg = "You're welcome, Sir!"
                self.tts.speak(msg)
                return {"success": True, "message": msg, "action": "thanks"}
            elif "who are you" in text_lower or "your name" in text_lower:
                count = self.registry.get_agent_count()
                msg = f"I am Nova, an advanced multi-agent AI system with {count} specialized agents. How may I help?"
                self.tts.speak(msg)
                return {"success": True, "message": msg, "action": "identity"}
        
        if matched_capability:
            agent = self.registry.find_best_agent(matched_capability)
            if agent:
                task = {
                    "action": matched_capability,
                    "parameters": {"raw_text": text},
                    "original_text": text
                }
                return agent.execute(task)
        
        # Absolute fallback
        self.tts.speak("I'm not sure how to handle that. Try asking differently.")
        return {"success": False, "message": "Unknown command", "action": "unknown"}
    
    # ── Agent Management (exposed for GUI) ────────────────────────────
    
    def get_agent_status(self) -> List[Dict]:
        """Get status of all agents for the GUI."""
        return self.registry.list_all()
    
    def get_agent_count(self) -> int:
        """Get total agent count."""
        return self.registry.get_agent_count()
    
    def get_memory_summary(self) -> Dict:
        """Get memory summary."""
        return self.memory.get_summary()
    
    def get_message_stats(self) -> Dict:
        """Get message bus stats."""
        return self.message_bus.get_stats()
    
    def shutdown(self):
        """Shut down the orchestrator and all agents."""
        self.logger.info("Orchestrator shutting down...")
        self.memory.save()
        self.registry.shutdown_all()
        self.message_bus.shutdown()
        self.logger.info("Orchestrator shut down complete.")
