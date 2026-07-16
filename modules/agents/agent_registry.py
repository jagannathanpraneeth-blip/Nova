"""
Nova Agent Registry
===================
Global registry that tracks all living agents in the system.
Thread-safe singleton that the Orchestrator uses to find and manage agents.
"""

import logging
import threading
from typing import Dict, List, Optional, Any


class AgentRegistry:
    """
    Singleton registry for all Nova agents.
    Provides thread-safe agent lifecycle management.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.logger = logging.getLogger("AgentRegistry")
        self._agents: Dict[str, Any] = {}  # agent_id -> Agent instance
        self._capability_index: Dict[str, List[str]] = {}  # capability -> [agent_ids]
        self._agents_lock = threading.RLock()
        self.logger.info("AgentRegistry initialized.")
    
    def register(self, agent) -> bool:
        """
        Register an agent in the system.
        Calls agent.initialize() and wires up references.
        
        Returns True if registration succeeded.
        """
        with self._agents_lock:
            if agent.agent_id in self._agents:
                self.logger.warning(f"Agent '{agent.agent_id}' already registered. Skipping.")
                return False
            
            # Wire up system references
            agent._registry = self
            
            # Initialize the agent
            try:
                success = agent.initialize()
                if not success:
                    self.logger.error(f"Agent '{agent.name}' failed to initialize.")
                    return False
            except Exception as e:
                self.logger.error(f"Agent '{agent.name}' initialization crashed: {e}")
                return False
            
            # Register in main index
            self._agents[agent.agent_id] = agent
            
            # Build capability index
            for cap in agent.get_capabilities():
                if cap not in self._capability_index:
                    self._capability_index[cap] = []
                self._capability_index[cap].append(agent.agent_id)
            
            self.logger.info(
                f"✓ Registered agent: {agent.name} ({agent.agent_id}) "
                f"with capabilities: {agent.get_capabilities()}"
            )
            return True
    
    def deregister(self, agent_id: str) -> bool:
        """Remove an agent from the system and shut it down."""
        with self._agents_lock:
            if agent_id not in self._agents:
                self.logger.warning(f"Agent '{agent_id}' not found in registry.")
                return False
            
            agent = self._agents[agent_id]
            
            # Remove from capability index
            for cap in agent.get_capabilities():
                if cap in self._capability_index:
                    self._capability_index[cap] = [
                        aid for aid in self._capability_index[cap] if aid != agent_id
                    ]
                    if not self._capability_index[cap]:
                        del self._capability_index[cap]
            
            # Shut down the agent
            try:
                agent.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down agent '{agent.name}': {e}")
            
            del self._agents[agent_id]
            self.logger.info(f"✗ Deregistered agent: {agent.name} ({agent_id})")
            return True
    
    def get_agent(self, agent_id: str):
        """Get an agent by its ID."""
        with self._agents_lock:
            return self._agents.get(agent_id)
    
    def get_agent_by_name(self, name: str):
        """Get the first agent matching a name."""
        with self._agents_lock:
            for agent in self._agents.values():
                if agent.name.lower() == name.lower():
                    return agent
            return None
    
    def get_agents_by_capability(self, capability: str) -> List:
        """Get all agents that have a specific capability."""
        with self._agents_lock:
            agent_ids = self._capability_index.get(capability, [])
            return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    def find_best_agent(self, capability: str):
        """
        Find the best agent for a capability.
        Prefers IDLE agents over BUSY ones, and those with fewer errors.
        """
        from modules.agents.agent_base import AgentState
        
        candidates = self.get_agents_by_capability(capability)
        if not candidates:
            return None
        
        # Sort by: state priority (IDLE first), then error count (fewer first)
        state_priority = {
            AgentState.IDLE: 0,
            AgentState.BUSY: 1,
            AgentState.WAITING: 2,
            AgentState.ERROR: 3,
            AgentState.TERMINATED: 4,
            AgentState.INITIALIZING: 5,
        }
        
        candidates.sort(key=lambda a: (state_priority.get(a.state, 99), a._error_count))
        return candidates[0]
    
    def list_all(self) -> List[Dict[str, Any]]:
        """Get descriptions of all registered agents."""
        with self._agents_lock:
            return [agent.describe() for agent in self._agents.values()]
    
    def list_capabilities(self) -> Dict[str, List[str]]:
        """Get the complete capability -> agents mapping."""
        with self._agents_lock:
            result = {}
            for cap, agent_ids in self._capability_index.items():
                result[cap] = [
                    self._agents[aid].name 
                    for aid in agent_ids 
                    if aid in self._agents
                ]
            return result
    
    def get_agent_count(self) -> int:
        """How many agents are currently registered."""
        with self._agents_lock:
            return len(self._agents)
    
    def get_healthy_agent_count(self) -> int:
        """How many agents are in a non-error state."""
        from modules.agents.agent_base import AgentState
        with self._agents_lock:
            return sum(
                1 for a in self._agents.values() 
                if a.state not in (AgentState.ERROR, AgentState.TERMINATED)
            )
    
    def get_manifest(self) -> str:
        """
        Generate a text manifest of all agents and capabilities.
        Used by the Orchestrator to tell the LLM what agents are available.
        """
        with self._agents_lock:
            lines = ["AVAILABLE AGENTS:"]
            for agent in self._agents.values():
                caps = ", ".join(agent.get_capabilities())
                lines.append(
                    f"  - {agent.name} (id={agent.agent_id}, state={agent.state.value}): "
                    f"{agent.description} | Capabilities: [{caps}]"
                )
            return "\n".join(lines)
    
    def wire_services(self, message_bus=None, memory=None, llm_engine=None):
        """
        Wire shared services into all currently registered agents.
        Called by the Orchestrator after setup.
        """
        with self._agents_lock:
            for agent in self._agents.values():
                if message_bus:
                    agent._message_bus = message_bus
                if memory:
                    agent._memory = memory
                if llm_engine:
                    agent._llm_engine = llm_engine
        self.logger.info("Services wired to all agents.")
    
    def shutdown_all(self):
        """Shut down all agents."""
        with self._agents_lock:
            for agent_id in list(self._agents.keys()):
                self.deregister(agent_id)
        self.logger.info("All agents shut down.")
    
    @classmethod
    def reset(cls):
        """Reset the singleton (for testing)."""
        with cls._lock:
            if cls._instance and hasattr(cls._instance, '_agents'):
                cls._instance.shutdown_all()
            cls._instance = None
