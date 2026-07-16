"""
Nova Shared Memory System
==========================
Centralized memory that all agents can read/write.
Persists to disk for cross-session continuity.
"""

import json
import logging
import threading
import time
import os
from typing import Any, Dict, List, Optional
from config import DATA_DIR


class SharedMemory:
    """
    Centralized memory store for the multi-agent system.
    
    Sections:
    - conversations: Chat history
    - agent_states: Current state of each agent
    - goals: Active goals and progress
    - preferences: Learned user preferences
    - knowledge: Facts the system has learned
    - task_history: What was tried and results
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
        self.logger = logging.getLogger("SharedMemory")
        
        self._store: Dict[str, Any] = {}
        self._store_lock = threading.RLock()
        self._memory_file = os.path.join(DATA_DIR, "memory.json")
        
        # Bounded sections
        self._max_conversations = 100
        self._max_task_history = 200
        self._max_knowledge = 500
        
        # Load from disk
        self._load()
        
        # Auto-save interval
        self._dirty = False
        self._save_thread = threading.Thread(
            target=self._auto_save_loop, daemon=True, name="Memory-AutoSave"
        )
        self._save_thread.start()
        
        self.logger.info("SharedMemory initialized.")
    
    # ── Core Operations ───────────────────────────────────────────────
    
    def store(self, key: str, value: Any):
        """
        Store a value. Uses dot-notation keys: 'section.subsection.key'
        """
        with self._store_lock:
            keys = key.split(".")
            current = self._store
            for k in keys[:-1]:
                if k not in current or not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
            self._dirty = True
    
    def retrieve(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value using dot-notation key.
        """
        with self._store_lock:
            keys = key.split(".")
            current = self._store
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return default
            return current
    
    def delete(self, key: str) -> bool:
        """Delete a key from the store."""
        with self._store_lock:
            keys = key.split(".")
            current = self._store
            for k in keys[:-1]:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return False
            if keys[-1] in current:
                del current[keys[-1]]
                self._dirty = True
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return self.retrieve(key) is not None
    
    # ── Conversation History ──────────────────────────────────────────
    
    def add_conversation(self, role: str, content: str, metadata: Dict = None):
        """Add a conversation entry."""
        with self._store_lock:
            if "conversations" not in self._store:
                self._store["conversations"] = []
            
            entry = {
                "role": role,
                "content": content,
                "timestamp": time.time(),
                "metadata": metadata or {}
            }
            self._store["conversations"].append(entry)
            
            # Bound the list
            if len(self._store["conversations"]) > self._max_conversations:
                self._store["conversations"] = self._store["conversations"][-self._max_conversations:]
            
            self._dirty = True
    
    def get_conversations(self, limit: int = 20) -> List[Dict]:
        """Get recent conversation history."""
        with self._store_lock:
            convos = self._store.get("conversations", [])
            return convos[-limit:]
    
    def get_conversation_context(self, limit: int = 10) -> str:
        """Get conversation history formatted as context string."""
        convos = self.get_conversations(limit)
        lines = []
        for c in convos:
            lines.append(f"{c['role']}: {c['content']}")
        return "\n".join(lines)
    
    # ── Goals ─────────────────────────────────────────────────────────
    
    def add_goal(self, goal_id: str, description: str, priority: int = 5):
        """Add a goal for the autonomous system to track."""
        with self._store_lock:
            if "goals" not in self._store:
                self._store["goals"] = {}
            
            self._store["goals"][goal_id] = {
                "description": description,
                "priority": priority,
                "status": "active",
                "progress": 0,
                "created_at": time.time(),
                "steps_completed": [],
                "steps_remaining": []
            }
            self._dirty = True
    
    def update_goal(self, goal_id: str, **updates):
        """Update a goal's status/progress."""
        with self._store_lock:
            if "goals" in self._store and goal_id in self._store["goals"]:
                self._store["goals"][goal_id].update(updates)
                self._dirty = True
    
    def get_active_goals(self) -> Dict[str, Dict]:
        """Get all active goals."""
        with self._store_lock:
            goals = self._store.get("goals", {})
            return {k: v for k, v in goals.items() if v.get("status") == "active"}
    
    # ── Task History ──────────────────────────────────────────────────
    
    def log_task(self, agent_name: str, action: str, success: bool, 
                 details: str = ""):
        """Log a completed task for learning."""
        with self._store_lock:
            if "task_history" not in self._store:
                self._store["task_history"] = []
            
            self._store["task_history"].append({
                "agent": agent_name,
                "action": action,
                "success": success,
                "details": details,
                "timestamp": time.time()
            })
            
            # Bound
            if len(self._store["task_history"]) > self._max_task_history:
                self._store["task_history"] = self._store["task_history"][-self._max_task_history:]
            
            self._dirty = True
    
    def get_task_history(self, agent_name: str = None, limit: int = 20) -> List[Dict]:
        """Get task history, optionally filtered by agent."""
        with self._store_lock:
            history = self._store.get("task_history", [])
            if agent_name:
                history = [t for t in history if t["agent"] == agent_name]
            return history[-limit:]
    
    # ── User Preferences ─────────────────────────────────────────────
    
    def set_preference(self, key: str, value: Any):
        """Store a user preference."""
        self.store(f"preferences.{key}", value)
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.retrieve(f"preferences.{key}", default)
    
    # ── Knowledge Base ────────────────────────────────────────────────
    
    def learn(self, fact_key: str, fact_value: Any):
        """Store a learned fact."""
        self.store(f"knowledge.{fact_key}", {
            "value": fact_value,
            "learned_at": time.time()
        })
    
    def get_knowledge(self, fact_key: str) -> Any:
        """Retrieve a learned fact."""
        fact = self.retrieve(f"knowledge.{fact_key}")
        if fact and isinstance(fact, dict):
            return fact.get("value")
        return fact
    
    # ── Persistence ───────────────────────────────────────────────────
    
    def _load(self):
        """Load memory from disk."""
        if os.path.exists(self._memory_file):
            try:
                with open(self._memory_file, "r", encoding="utf-8") as f:
                    self._store = json.load(f)
                self.logger.info(f"Loaded memory from {self._memory_file}")
            except Exception as e:
                self.logger.error(f"Failed to load memory: {e}")
                self._store = {}
        else:
            self._store = {}
    
    def save(self):
        """Save memory to disk."""
        with self._store_lock:
            try:
                # Make a serializable copy
                serializable = self._make_serializable(self._store)
                with open(self._memory_file, "w", encoding="utf-8") as f:
                    json.dump(serializable, f, indent=2, ensure_ascii=False)
                self._dirty = False
            except Exception as e:
                self.logger.error(f"Failed to save memory: {e}")
    
    def _make_serializable(self, obj):
        """Recursively convert objects to JSON-serializable types."""
        if isinstance(obj, dict):
            return {str(k): self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)
    
    def _auto_save_loop(self):
        """Auto-save dirty memory every 30 seconds."""
        while True:
            time.sleep(30)
            if self._dirty:
                self.save()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of memory contents."""
        with self._store_lock:
            return {
                "conversations": len(self._store.get("conversations", [])),
                "goals_active": len(self.get_active_goals()),
                "task_history": len(self._store.get("task_history", [])),
                "preferences": len(self._store.get("preferences", {})),
                "knowledge_facts": len(self._store.get("knowledge", {})),
                "total_keys": self._count_keys(self._store)
            }
    
    def _count_keys(self, d, depth=0) -> int:
        """Count total keys in nested dict."""
        if not isinstance(d, dict) or depth > 10:
            return 0
        count = len(d)
        for v in d.values():
            if isinstance(v, dict):
                count += self._count_keys(v, depth + 1)
        return count
    
    @classmethod
    def reset(cls):
        """Reset the singleton (for testing)."""
        with cls._lock:
            cls._instance = None
