"""
Nova Agent Base Class
=====================
The foundation of the multi-agent system.
Every agent (built-in or dynamically created) inherits from this class.
"""

import logging
import threading
import uuid
import time
from typing import Dict, Any, List, Optional
from enum import Enum


class AgentState(Enum):
    """Possible states an agent can be in."""
    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    WAITING = "waiting"
    ERROR = "error"
    TERMINATED = "terminated"


class AgentMessage:
    """A message that can be sent between agents."""
    
    def __init__(self, sender_id: str, recipient_id: str, msg_type: str,
                 content: Any, priority: int = 5, correlation_id: str = None):
        self.id = str(uuid.uuid4())[:8]
        self.sender_id = sender_id
        self.recipient_id = recipient_id  # "*" for broadcast
        self.msg_type = msg_type  # TASK, RESULT, STATUS, ERROR, QUERY
        self.content = content
        self.priority = priority  # 1 = highest, 10 = lowest
        self.correlation_id = correlation_id or self.id
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "msg_type": self.msg_type,
            "content": self.content,
            "priority": self.priority,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp
        }


class Agent:
    """
    Base class for all Nova agents.
    
    Every agent has:
    - An identity (name, description, capabilities)
    - A lifecycle (initialize, execute, shutdown)
    - Communication abilities (send/receive messages)
    - State management
    - Access to shared memory and LLM
    """
    
    def __init__(self, agent_id: str = None, name: str = "BaseAgent",
                 description: str = "A Nova agent", **kwargs):
        self.agent_id = agent_id or f"{name.lower().replace(' ', '_')}_{str(uuid.uuid4())[:6]}"
        self.name = name
        self.description = description
        self.capabilities: List[str] = []
        self.state = AgentState.INITIALIZING
        self.logger = logging.getLogger(f"Agent.{self.name}")
        
        # References set by the registry/orchestrator after creation
        self._message_bus = None
        self._memory = None
        self._llm_engine = None
        self._registry = None
        
        # Internal state
        self._inbox = []
        self._inbox_lock = threading.Lock()
        self._current_task = None
        self._task_history: List[Dict] = []
        self._error_count = 0
        self._max_errors = 5
        self._created_at = time.time()
        
        self.logger.info(f"Agent '{self.name}' ({self.agent_id}) created.")
    
    # ── Lifecycle ─────────────────────────────────────────────────────
    
    def initialize(self) -> bool:
        """
        Called once when the agent is registered.
        Override in subclasses to set up resources.
        Returns True if initialization succeeded.
        """
        self.state = AgentState.IDLE
        self.logger.info(f"Agent '{self.name}' initialized.")
        return True
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task. This is the main entry point for work.
        
        Args:
            task: Dict with at least {"action": str, "parameters": dict}
        
        Returns:
            Dict with {"success": bool, "message": str, "data": any}
        """
        self.state = AgentState.BUSY
        self._current_task = task
        
        try:
            result = self._do_execute(task)
            self._task_history.append({
                "task": task,
                "result": result,
                "timestamp": time.time()
            })
            # Keep history bounded
            if len(self._task_history) > 50:
                self._task_history = self._task_history[-50:]
            self._error_count = 0
            return result
        except Exception as e:
            self._error_count += 1
            self.logger.error(f"Agent '{self.name}' execution error: {e}", exc_info=True)
            if self._error_count >= self._max_errors:
                self.state = AgentState.ERROR
                self.logger.critical(f"Agent '{self.name}' exceeded max errors ({self._max_errors}). Entering ERROR state.")
            else:
                self.state = AgentState.IDLE
            return {"success": False, "message": f"Agent error: {str(e)}", "action": "error"}
        finally:
            if self.state == AgentState.BUSY:
                self.state = AgentState.IDLE
            self._current_task = None
    
    def _do_execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Override this in subclasses to implement actual logic.
        """
        raise NotImplementedError(f"Agent '{self.name}' must implement _do_execute()")
    
    def shutdown(self):
        """
        Clean up resources. Called when agent is deregistered.
        """
        self.state = AgentState.TERMINATED
        self.logger.info(f"Agent '{self.name}' shut down.")
    
    # ── Communication ─────────────────────────────────────────────────
    
    def send_message(self, recipient_id: str, msg_type: str, content: Any, 
                     priority: int = 5):
        """Send a message to another agent via the message bus."""
        if self._message_bus:
            msg = AgentMessage(
                sender_id=self.agent_id,
                recipient_id=recipient_id,
                msg_type=msg_type,
                content=content,
                priority=priority
            )
            self._message_bus.publish(msg)
            return msg.id
        else:
            self.logger.warning("No message bus connected. Message not sent.")
            return None
    
    def receive_message(self, msg: 'AgentMessage'):
        """Called by the message bus when a message arrives for this agent."""
        with self._inbox_lock:
            self._inbox.append(msg)
    
    def get_messages(self, msg_type: str = None) -> List['AgentMessage']:
        """Get and clear messages from inbox, optionally filtered by type."""
        with self._inbox_lock:
            if msg_type:
                matched = [m for m in self._inbox if m.msg_type == msg_type]
                self._inbox = [m for m in self._inbox if m.msg_type != msg_type]
                return matched
            else:
                msgs = list(self._inbox)
                self._inbox.clear()
                return msgs
    
    def broadcast(self, msg_type: str, content: Any):
        """Broadcast a message to all agents."""
        self.send_message("*", msg_type, content)
    
    # ── Capability Declaration ────────────────────────────────────────
    
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides."""
        return self.capabilities
    
    def can_handle(self, action: str) -> bool:
        """Check if this agent can handle a specific action."""
        return action in self.capabilities
    
    def describe(self) -> Dict[str, Any]:
        """Return a full description of this agent for the orchestrator."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "state": self.state.value,
            "error_count": self._error_count,
            "current_task": self._current_task is not None,
            "tasks_completed": len(self._task_history),
            "uptime_seconds": round(time.time() - self._created_at)
        }
    
    # ── LLM Access ────────────────────────────────────────────────────
    
    def ask_llm(self, prompt: str, system_prompt: str = None) -> str:
        """
        Ask the LLM a question. Available to all agents for reasoning.
        Returns the raw text response.
        """
        if not self._llm_engine or not self._llm_engine.provider:
            return ""
        
        try:
            if self._llm_engine.provider == "gemini":
                import google.generativeai as genai
                model = genai.GenerativeModel(self._llm_engine.model_name)
                full = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                response = model.generate_content(full)
                return response.text
            elif self._llm_engine.provider == "openai":
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                response = self._llm_engine.client.chat.completions.create(
                    model=self._llm_engine.model_name,
                    messages=messages,
                    temperature=0.7
                )
                return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"LLM query failed: {e}")
            return ""
    
    def ask_llm_json(self, prompt: str, system_prompt: str = None) -> Dict:
        """Ask the LLM and parse the response as JSON."""
        import json
        raw = self.ask_llm(prompt, system_prompt)
        if not raw:
            return {}
        
        # Clean up code blocks
        text = raw
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse LLM JSON: {text[:200]}")
            return {}
    
    # ── Memory Access ─────────────────────────────────────────────────
    
    def remember(self, key: str, value: Any):
        """Store something in shared memory."""
        if self._memory:
            self._memory.store(f"agent.{self.agent_id}.{key}", value)
    
    def recall(self, key: str) -> Any:
        """Recall something from shared memory."""
        if self._memory:
            return self._memory.retrieve(f"agent.{self.agent_id}.{key}")
        return None
    
    # ── String Representation ─────────────────────────────────────────
    
    def __repr__(self):
        return f"<Agent '{self.name}' [{self.state.value}] caps={self.capabilities}>"
