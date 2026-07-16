"""
Nova Message Bus
================
Publish/subscribe inter-agent communication system.
Supports direct messaging, broadcasts, and priority queues.
"""

import logging
import threading
import queue
import time
from typing import Dict, List, Callable, Optional, Any


class MessageBus:
    """
    Central message bus for agent-to-agent communication.
    
    Features:
    - Direct agent-to-agent messaging
    - Broadcast messages (recipient_id = "*")
    - Priority queue (lower number = higher priority)
    - Subscriber callbacks for specific message types
    - Message history for debugging
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
        self.logger = logging.getLogger("MessageBus")
        
        # Agent registry reference (set by orchestrator)
        self._registry = None
        
        # Subscriber callbacks: {msg_type: [callback_fn, ...]}
        self._subscribers: Dict[str, List[Callable]] = {}
        self._sub_lock = threading.Lock()
        
        # Message history (bounded)
        self._history: List[Dict] = []
        self._history_lock = threading.Lock()
        self._max_history = 200
        
        # Processing queue for async delivery
        self._queue = queue.PriorityQueue()
        self._running = True
        self._delivery_thread = threading.Thread(
            target=self._delivery_loop, daemon=True, name="MessageBus-Delivery"
        )
        self._delivery_thread.start()
        
        self.logger.info("MessageBus initialized.")
    
    def set_registry(self, registry):
        """Set the agent registry reference for message delivery."""
        self._registry = registry
    
    def publish(self, message):
        """
        Publish a message to the bus.
        Messages are queued and delivered asynchronously.
        """
        # Queue with priority (lower = higher priority)
        self._queue.put((message.priority, time.time(), message))
        
        # Record in history
        with self._history_lock:
            self._history.append(message.to_dict())
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
    
    def _delivery_loop(self):
        """Background thread that delivers messages from the queue."""
        while self._running:
            try:
                priority, timestamp, message = self._queue.get(timeout=0.5)
                self._deliver(message)
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Message delivery error: {e}", exc_info=True)
    
    def _deliver(self, message):
        """Deliver a message to its recipient(s)."""
        if not self._registry:
            self.logger.warning("No registry connected. Message dropped.")
            return
        
        # Broadcast
        if message.recipient_id == "*":
            for agent_info in self._registry.list_all():
                agent = self._registry.get_agent(agent_info["agent_id"])
                if agent and agent.agent_id != message.sender_id:
                    try:
                        agent.receive_message(message)
                    except Exception as e:
                        self.logger.error(f"Broadcast delivery error to {agent.name}: {e}")
        else:
            # Direct delivery
            agent = self._registry.get_agent(message.recipient_id)
            if agent:
                try:
                    agent.receive_message(message)
                except Exception as e:
                    self.logger.error(
                        f"Direct delivery error to {message.recipient_id}: {e}"
                    )
            else:
                self.logger.warning(
                    f"Recipient '{message.recipient_id}' not found. Message dropped."
                )
        
        # Notify subscribers
        self._notify_subscribers(message)
    
    def subscribe(self, msg_type: str, callback: Callable):
        """
        Subscribe to messages of a specific type.
        Callback receives the message object.
        """
        with self._sub_lock:
            if msg_type not in self._subscribers:
                self._subscribers[msg_type] = []
            self._subscribers[msg_type].append(callback)
            self.logger.debug(f"Subscriber added for '{msg_type}'")
    
    def unsubscribe(self, msg_type: str, callback: Callable):
        """Remove a subscriber callback."""
        with self._sub_lock:
            if msg_type in self._subscribers:
                self._subscribers[msg_type] = [
                    cb for cb in self._subscribers[msg_type] if cb != callback
                ]
    
    def _notify_subscribers(self, message):
        """Notify all subscribers of this message type."""
        with self._sub_lock:
            callbacks = self._subscribers.get(message.msg_type, [])
        
        for callback in callbacks:
            try:
                callback(message)
            except Exception as e:
                self.logger.error(f"Subscriber callback error: {e}")
    
    def get_history(self, limit: int = 50, msg_type: str = None) -> List[Dict]:
        """Get recent message history, optionally filtered by type."""
        with self._history_lock:
            if msg_type:
                filtered = [m for m in self._history if m["msg_type"] == msg_type]
                return filtered[-limit:]
            return self._history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics."""
        with self._history_lock:
            type_counts = {}
            for msg in self._history:
                t = msg["msg_type"]
                type_counts[t] = type_counts.get(t, 0) + 1
            
            return {
                "total_messages": len(self._history),
                "pending_delivery": self._queue.qsize(),
                "message_types": type_counts,
                "subscriber_count": sum(len(cbs) for cbs in self._subscribers.values())
            }
    
    def shutdown(self):
        """Stop the message bus."""
        self._running = False
        self._delivery_thread.join(timeout=2)
        self.logger.info("MessageBus shut down.")
    
    @classmethod
    def reset(cls):
        """Reset the singleton (for testing)."""
        with cls._lock:
            if cls._instance:
                cls._instance.shutdown()
            cls._instance = None
